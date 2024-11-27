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
from rest_framework.exceptions import NotFound
from .serializers import CommitteSerializer, SubCommitteeSerializer, CommitteeDetailsSerializer, CommitteSerializerForFetch


from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa


# class CreateCommittee(APIView):
#     def post(self, request):
#         committee_data = request.data.get('committee')
#         if not committee_data:
#             return Response({'error': 'Committee data is required.'}, status=status.HTTP_400_BAD_REQUEST)

#         subcommittees_data = request.data.get('subcommittees', [])
#         members_data = request.data.get('members', [])

#         logger.info(f'Received committee data: {committee_data}')
#         logger.info(f'Received members data: {members_data}')
#         logger.info(f'Received subcommittees data: {subcommittees_data}')

#         committee_serializer = CommitteSerializer(data=committee_data)
#         if committee_serializer.is_valid():
#             with transaction.atomic():
#                 # Save the main committee
#                 committee = committee_serializer.save()

#                 # Process main committee members (those without subcommittee_id)
#                 for member_data in members_data:
#                     if not member_data.get('subcommittee_id'):
#                         member_data['committee_id'] = committee.id
#                         member_serializer = CommitteeDetailsSerializer(data=member_data)
#                         if member_serializer.is_valid():
#                             member_serializer.save()
#                         else:
#                             return Response({
#                                 'error': 'Member validation failed.',
#                                 'details': member_serializer.errors
#                             }, status=status.HTTP_400_BAD_REQUEST)

#                 # Process each subcommittee and its members
#                 for sub_data in subcommittees_data:
#                     sub_data['committee_id'] = committee.id
#                     subcommittee_serializer = SubCommitteeSerializer(data=sub_data)
#                     if subcommittee_serializer.is_valid():
#                         subcommittee = subcommittee_serializer.save()

#                         # Process members specific to this subcommittee
#                         for member_data in members_data:
#                             if member_data.get('subcommittee_id') == sub_data.get('subcommittee_id'):
#                                 member_data['committee_id'] = committee.id
#                                 member_data['subcommittee_id'] = subcommittee.id
#                                 member_serializer = CommitteeDetailsSerializer(data=member_data)
#                                 if member_serializer.is_valid():
#                                     member_serializer.save()
#                                 else:
#                                     return Response({
#                                         'error': 'Subcommittee member validation failed.',
#                                         'details': member_serializer.errors
#                                     }, status=status.HTTP_400_BAD_REQUEST)
#                     else:
#                         return Response({
#                             'error': 'Subcommittee validation failed.',
#                             'details': subcommittee_serializer.errors
#                         }, status=status.HTTP_400_BAD_REQUEST)

#             return Response(committee_serializer.data, status=status.HTTP_201_CREATED)

#         return Response({
#             'error': 'Committee validation failed.',
#             'details': committee_serializer.errors
#         }, status=status.HTTP_400_BAD_REQUEST)

class CreateCommittee(APIView):
    def post(self, request):
        serializer = CommitteSerializer(data=request.data)
        if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': 'Committee validation failed.',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
class DeleteCommittee(APIView):
    def delete(self, request, committee_id):
        try:
            # Retrieve the committee by its ID
            committee = Committe.objects.get(id=committee_id)
            committee.delete()  # Delete the committee
            return Response({'message': 'Committee deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)
        except Committe.DoesNotExist:
            # If committee doesn't exist, return a 404 not found response
            raise NotFound(detail="Committee not found.")
        


        



class AddMainCommitteeMembers(APIView):
    def post(self, request):
        committee_id = request.data.get("committee_id")
        members = request.data.get("members", [])

        # Check if committee exists
        try:
            committee = Committe.objects.get(id=committee_id)
        except Committe.DoesNotExist:
            return Response(
                {"error": "Committee not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Add each member to CommitteeDetails
        errors = []
        for member in members:
            serializer = CommitteeDetailsSerializer(data={
                "committee_id": committee_id,
                "employee_id": member.get("employee_id"),
                "role": member.get("role"),
                "score": member.get("score"),
                  # Associate member with committee
            })
            if serializer.is_valid():
                serializer.save()
            else:
                errors.append({
                    "employee_id": member.get("employee_id"),
                    "errors": serializer.errors
                })

        if errors:
            return Response(
                {"error": "Some members failed validation.", "details": errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({"message": "Main committee members added successfully."}, status=status.HTTP_201_CREATED)
    def delete(self, request,id):
        committee_detail_id = request.data.get("id")

        # Check if the CommitteeDetails entry exists
        try:
            committee_detail = CommitteeDetails.objects.get(id=id)
            committee_detail.delete()  # Remove the committee member entry
        except CommitteeDetails.DoesNotExist:
            return Response(
                {"error": "Committee member not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({"message": "Member removed successfully."}, status=status.HTTP_204_NO_CONTENT)


class SubCommitteeCreateView(APIView):
    def post(self, request, committee_id):
        try:
            committee = Committe.objects.get(id=committee_id)
        except Committe.DoesNotExist:
            return Response({"error": "Committee not found."}, status=status.HTTP_404_NOT_FOUND)

        # Create a new SubCommittee instance
        serializer = SubCommitteeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(committee_id=committee)  # Set the committee foreign key
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class SubCommitteeRetrieveView(APIView):
    def get(self, request, committee_id, subcommittee_id):
        try:
            # Fetch the committee to ensure it exists (optional, if needed)
            committee = Committe.objects.get(id=committee_id)

            # Fetch the specific subcommittee
            subcommittee = SubCommittee.objects.get(id=subcommittee_id, committee_id=committee)

        except Committe.DoesNotExist:
            return Response({"error": "Committee not found."}, status=status.HTTP_404_NOT_FOUND)
        except SubCommittee.DoesNotExist:
            return Response({"error": "Subcommittee not found."}, status=status.HTTP_404_NOT_FOUND)

        # Serialize the subcommittee data
        serializer = SubCommitteeSerializer(subcommittee)

        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
class EditSubCommitteeView(APIView):
    def put(self, request, subcommittee_id):
        try:
          
            subcommittee = SubCommittee.objects.get(id=subcommittee_id)
        except SubCommittee.DoesNotExist:
            return Response({"error": "Subcommittee not found."}, status=status.HTTP_404_NOT_FOUND)

      
        serializer = SubCommitteeSerializer(subcommittee, data=request.data, partial=True)  # `partial=True` allows partial updates
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class AddSubcommitteeMemberView(APIView):
    def post(self, request, subcommittee_id):
        try:
            subcommittee = SubCommittee.objects.get(id=subcommittee_id)
        except SubCommittee.DoesNotExist:
            return Response({"error": "Subcommittee not found"}, status=status.HTTP_404_NOT_FOUND)
        if 'members' not in request.data:
            return Response({"error": "No members data provided"}, status=status.HTTP_400_BAD_REQUEST)

        for member in request.data['members']:
            serializer = CommitteeDetailsSerializer(data=member)
            if serializer.is_valid():
                serializer.save(subcommittee_id=subcommittee)  # Save with the associated subcommittee
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Members added successfully"}, status=status.HTTP_201_CREATED)

class DeleteSubcommitteeMemberView(APIView):
    def delete(self, request, subcommittee_id, member_id):
        """
        Deletes a member from the specified subcommittee.
        """
        try:
            # Fetching the member associated with the subcommittee
            member = CommitteeDetails.objects.get(id=member_id, subcommittee_id=subcommittee_id)
        except CommitteeDetails.DoesNotExist:
            return Response(
                {"error": "Member not found in the specified subcommittee"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Delete the member
        member.delete()
        return Response(
            {"message": "Member removed successfully"},
            status=status.HTTP_200_OK,
        )



class ListCommittees(APIView):
    def get(self, request):
        # Fetch all committees
        committees = Committe.objects.all().order_by('-id')
        serializer = CommitteSerializerForFetch(committees, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class EditCommittee(APIView):
    def put(self, request, committee_id):
        committee = get_object_or_404(Committe, id=committee_id)
        serializer = CommitteSerializer(committee, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Committee validation failed.',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    

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
    receiver_name = request.GET.get('receiver_name')
    copy_name = request.GET.get('copy_name')
    role = request.GET.get('role')
    
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
            'role': role,
            'copy_name': copy_name,
            'receiver_name': receiver_name,
            'is_pdf': True,  # Flag to indicate PDF rendering
        }

        # Render the HTML template with the context
        html = render_to_string('committee_report_template.html', context)
        return HttpResponse(html)

    else:
        return HttpResponse('Committee not found', status=404)
    

# def generate_committee_word(request, committee_id):
#     # Create an instance of the CommitteeDetailView
#     detail_view = CommitteeDetailView()
#     response = detail_view.get(request, committee_id)
#     receiver_name = request.GET.get('receiver_name')
#     copy_name = request.GET.get('copy_name')
#     role = request.GET.get('role')

#     if response.status_code == status.HTTP_200_OK:
#         committee_data = response.data

#         # Prepare the context with the necessary data
#         context = {
#             'order_number': committee_data.get('order_number'),
#             'committe_name': committee_data.get('committe_Name'), 
#             'order_date': committee_data.get('order_date'),
#             'order_text': committee_data.get('order_Text'),
#             'order_description': committee_data.get('order_Description'),
#             'committe_expiry': committee_data.get('committe_Expiry'),
#             'main_members': committee_data.get('main_committee_members'),
#             'sub_committees': committee_data.get('sub_committees'),
#             'role': role,
#             'copy_name': copy_name,
#             'receiver_name': receiver_name,
#         }

#         # Render the HTML template with the context
#         html_content = render_to_string('committee_report_template.html', context)

#         # Parse the HTML content
#         soup = BeautifulSoup(html_content, 'html.parser')

#         # Create a Word document
#         document = Document()
#         document.add_heading('Committee Report', level=1)

#         # Add content to the Word document
#         for element in soup.descendants:
#             if element.name == 'h1':
#                 document.add_heading(element.text, level=1)
#             elif element.name == 'h2':
#                 document.add_heading(element.text, level=2)
#             elif element.name == 'p':
#                 document.add_paragraph(element.text)
#             elif element.name == 'ul':  # Handle unordered lists
#                 for li in element.find_all('li'):
#                     document.add_paragraph(f"• {li.text}", style='List Bullet')

#         # Convert the Word document to a binary stream
#         file_stream = BytesIO()
#         document.save(file_stream)
#         file_stream.seek(0)

#         # Serve the Word document as an HTTP response
#         response = HttpResponse(file_stream, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
#         response['Content-Disposition'] = f'attachment; filename=committee_report_{committee_id}.docx'

#         return response

#     else:
#         return HttpResponse('Committee not found', status=404)