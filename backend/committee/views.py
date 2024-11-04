from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Committe, CommitteeDetails, SubCommittee, Employee
from .serializers import CommitteSerializer, CommitteeDetailsSerializer, SubCommitteeSerializer, SubCommitteeSerializerForFetch
from django.shortcuts import get_object_or_404


import logging
logger = logging.getLogger(__name__)

from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import CommitteSerializer, SubCommitteeSerializer, CommitteeDetailsSerializer, CommitteSerializerForFetch


from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa


class CreateCommittee(APIView):
    def post(self, request):
        committee_data = request.data.get('committee')
        if not committee_data:
            return Response({'error': 'Committee data is required.'}, status=status.HTTP_400_BAD_REQUEST)

        subcommittees_data = request.data.get('subcommittees', [])
        members_data = request.data.get('members', [])

        logger.info(f'Received committee data: {committee_data}')
        logger.info(f'Received members data: {members_data}')
        logger.info(f'Received subcommittees data: {subcommittees_data}')

        committee_serializer = CommitteSerializer(data=committee_data)
        if committee_serializer.is_valid():
            with transaction.atomic():
                # Save the main committee
                committee = committee_serializer.save()

                # Process main committee members (those without subcommittee_id)
                for member_data in members_data:
                    if not member_data.get('subcommittee_id'):
                        member_data['committee_id'] = committee.id
                        member_serializer = CommitteeDetailsSerializer(data=member_data)
                        if member_serializer.is_valid():
                            member_serializer.save()
                        else:
                            return Response({
                                'error': 'Member validation failed.',
                                'details': member_serializer.errors
                            }, status=status.HTTP_400_BAD_REQUEST)

                # Process each subcommittee and its members
                for sub_data in subcommittees_data:
                    sub_data['committee_id'] = committee.id
                    subcommittee_serializer = SubCommitteeSerializer(data=sub_data)
                    if subcommittee_serializer.is_valid():
                        subcommittee = subcommittee_serializer.save()

                        # Process members specific to this subcommittee
                        for member_data in members_data:
                            if member_data.get('subcommittee_id') == sub_data.get('subcommittee_id'):
                                member_data['committee_id'] = committee.id
                                member_data['subcommittee_id'] = subcommittee.id
                                member_serializer = CommitteeDetailsSerializer(data=member_data)
                                if member_serializer.is_valid():
                                    member_serializer.save()
                                else:
                                    return Response({
                                        'error': 'Subcommittee member validation failed.',
                                        'details': member_serializer.errors
                                    }, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        return Response({
                            'error': 'Subcommittee validation failed.',
                            'details': subcommittee_serializer.errors
                        }, status=status.HTTP_400_BAD_REQUEST)

            return Response(committee_serializer.data, status=status.HTTP_201_CREATED)

        return Response({
            'error': 'Committee validation failed.',
            'details': committee_serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)



class ListCommittees(APIView):
    def get(self, request):
        # Fetch all committees
        committees = Committe.objects.all()
        serializer = CommitteSerializerForFetch(committees, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class CommitteeDetailView(APIView):
    def get(self, request, pk):
        try:
            # Fetch the specific committee by ID
            committee = Committe.objects.get(id=pk)
            serializer = CommitteSerializerForFetch(committee)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Committe.DoesNotExist:
            return Response({"error": "Committee not found"}, status=status.HTTP_404_NOT_FOUND)


def generate_committee_report(request, committee_id):
    # Create an instance of the CommitteeDetailView
    detail_view = CommitteeDetailView()
    response = detail_view.get(request, committee_id)

    if response.status_code == status.HTTP_200_OK:
        committee_data = response.data

        # Prepare the context with the necessary data
        context = {
            'order_number': committee_data.get('order_number'),
            'committe_name': committee_data.get('committe_Name'),
            'order_date': committee_data.get('order_date'),
            'order_text': committee_data.get('order_Text'),
            'order_description': committee_data.get('order_Description'),
            'committe_expiry': committee_data.get('committe_Expiry'),
            'main_members': committee_data.get('main_committee_members'),
            'sub_committees': committee_data.get('sub_committees'),
        }

        # Render the HTML template with the context
        html = render_to_string('committee_report_template.html', context)

        # Create a PDF response
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="committee_report_{committee_id}.pdf"'

        # Generate PDF
        pisa_status = pisa.CreatePDF(html, dest=response)

        # Check for errors
        if pisa_status.err:
            return HttpResponse('We had some errors <pre>' + html + '</pre>')

        return response
    else:
        return HttpResponse('Committee not found', status=404)