#———employee view————————
from django.shortcuts import render
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q,Sum
from rest_framework import status
from .models import Designation,Department,Employee,Qualification,EmployeeQualification
from .serializers import DesignationSerializer,DepartmentSerializer,EmployeeSerializers,QualificationSerializers,EmployeeQualificationSerializers,EmployeefilterSerializers
from leave_management.models import LeaveDetails
from committee.models import CommitteeDetails
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
from collections import defaultdict


class EmployeeView(APIView):
    def get(self, request):
        employees = Employee.objects.all()
        serializer = EmployeeSerializers(employees, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = EmployeeSerializers(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DesignationView(generics.ListAPIView):
   def get(self, request):
        designation = Designation.objects.all()
        serializer = DesignationSerializer(designation, many=True)
        return Response(serializer.data)
class DepartmentView(APIView):
     def get(self, request):
        department = Department.objects.all()
        serializer = DepartmentSerializer(department, many=True)
        return Response(serializer.data)
     

class QualificationView(APIView):

    def get(self, request):
        qualifications = Qualification.objects.all()
        serializer = QualificationSerializers(qualifications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = QualificationSerializers(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)     
    

class EmployeeQualificationView(APIView):

    def get(self, request):
        employee_qualifications = EmployeeQualification.objects.all()
        serializer = EmployeeQualificationSerializers(employee_qualifications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = EmployeeQualificationSerializers(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





class AvailableEmployeeListViewByScore(APIView):
    def get(self, request):
        # Get query parameters
        department = request.GET.get('department')
        emp_type = request.GET.get('type')

        # Start with the base queryset
        queryset = Employee.objects.all()

        # Apply department filter if provided
        if department:
            queryset = queryset.filter(department_id=department)

        # Apply employee type filter if provided and valid
        if emp_type and emp_type.isdigit():
            queryset = queryset.filter(type=int(emp_type))

        # Exclude employees who are currently on leave
        today = timezone.now().date()
        queryset = queryset.exclude(
            leave_details__start_date__lte=today,
            leave_details__end_date__gte=today
        )

        # Annotate total score, set to 0 if no score exists, and filter active committees 
        employees_with_scores = (
            queryset
            .annotate(
                total_score=Coalesce(
                    Sum('committees_employee__score', filter=Q(committees_employee__committee_id__is_active=True)),
                    Value(0)
                )
            )
            .select_related('department')
            .order_by('total_score')
        )

        # Preparing response data
        response_data = [
            {
                'employee_id': emp.id,
                'employee_name': emp.name,
                'department_name': emp.department.department_name if emp.department else None,
                'designation_name': emp.designation.designation_name if emp.designation else None,
                'total_score': emp.total_score
            }
            for emp in employees_with_scores
        ]

        return Response(response_data, status=status.HTTP_200_OK)
    


class EmployeesInCommitteesView(APIView):
    def get(self, request):
        committee_id = request.GET.get('committee_id')
        department = request.GET.get('department')
        emp_type = request.GET.get('type')

        # Initialize the queryset
        queryset = CommitteeDetails.objects.all().select_related('employee_id', 'committee_id', 'subcommittee_id')

        # Apply filters based on query parameters
        if committee_id:
            queryset = queryset.filter(Q(committee_id=committee_id) | Q(subcommittee_id=committee_id))

        if department:
            queryset = queryset.filter(employee_id__department_id=department)

        if emp_type and emp_type.isdigit():
            queryset = queryset.filter(employee_id__type=emp_type)

        # Initialize a dictionary to group data by employee
        employees = defaultdict(lambda: {
            'employee_id': None,
            'employee_name': None,
            'committees': []
        })

        # Process the queryset to group by employee
        for detail in queryset:
            employee = employees[detail.employee_id.id]
            if not employee['employee_id']:
                employee['employee_id'] = detail.employee_id.id
                employee['employee_name'] = detail.employee_id.name

            # Add each committee they are a part of
            employee['committees'].append({
                'committee_name': detail.committee_id.committe_Name if detail.committee_id else None,
                'subcommittee_name': detail.subcommittee_id.sub_committee_name if detail.subcommittee_id else None,
                'role': detail.role,
                'score': detail.score
            })

        # Prepare the response data
        response_data = list(employees.values())

        return Response(response_data, status=status.HTTP_200_OK)


#----filtering employees those are not on leave ----------------------
# class AvailableEmployeeListView(APIView):
#     serializer_class = EmployeefilterSerializers

#     def get_queryset(self):
#         today = timezone.now().date()

#         # Exclude employees currently on leave
#         queryset = Employee.objects.exclude(
#             id__in=Leave.objects.filter(
#                 start_date__lte=today,
#                 end_date__gte=today
#             ).values('employee_id')
#         )

#         return queryset   

#----------------------to get highest qualification of an employee----------------------
    #  def get_highest_qualification(employee_id):
    # highest_qualification = (
    #     EmployeeQualification.objects
    #     .filter(employee_id=employee_id)
    #     .select_related('qualification')
    #     .order_by('-qualification__rank')
    #     .first()
    # )
    # return highest_qualification.qualification if highest_qualification else None
#—————————————————————————————————————