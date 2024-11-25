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
from django.db.models import Sum, F
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.utils import get_column_letter

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
        # Get query parameters
        committee_id = request.GET.get('committee_id')
        department = request.GET.get('department')
        emp_type = request.GET.get('type')
        search_query = request.GET.get('search')  # New search parameter

        # Initialize the queryset
        queryset = CommitteeDetails.objects.all().select_related('employee_id', 'committee_id', 'subcommittee_id')

        # Apply filters based on query parameters
        if committee_id:
            queryset = queryset.filter(Q(committee_id=committee_id) | Q(subcommittee_id=committee_id))

        if department:
            queryset = queryset.filter(employee_id__department_id=department)

        if emp_type and emp_type.isdigit():
            queryset = queryset.filter(employee_id__type=emp_type)

        if search_query:  # Apply search filter
            queryset = queryset.filter(
                Q(employee_id__name__icontains=search_query) |
                Q(employee_id__email__icontains=search_query)  # Example: filter by name or email
            )

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
    

class EmployeeReportAPIView(APIView):
    """
    API View to fetch the employee report with aggregated scores, 
    including employees who are not in any committee, with filtering by type and showing department.
    """
    def get(self, request):
        try:
            # Get the 'type' query parameter from the request
            emp_type = request.GET.get('type')
            order = request.GET.get('order', 'desc').lower()  # Default to 'desc'

            # Validate 'order' parameter
            if order not in ['asc', 'desc']:
                return Response({"error": "Invalid 'order' parameter. Use 'asc' or 'desc'."}, status=status.HTTP_400_BAD_REQUEST)

            # Fetch employees in committees and aggregate scores
            employees_in_committee = (
                CommitteeDetails.objects
                .filter(committee_id__isnull=False)  # Ensure they are in a committee
                .values(
                    employee_unique_id=F('employee_id__id'),  # Unique name for the field
                    employee_name=F('employee_id__name'),
                    employee_type=F('employee_id__type'),  # Include type
                    department_name=F('employee_id__department__department_name')  # Include department name
                )
                .annotate(
                    total_score=Sum('score')  # Aggregate scores
                )
            )

            # Fetch employees not in any committee
            employees_not_in_committee = (
                Employee.objects
                .exclude(
                    id__in=CommitteeDetails.objects.values_list('employee_id', flat=True)  # Exclude those in committees
                )
                .values(
                    employee_unique_id=F('id'),  # Match field naming with the above
                    employee_name=F('name'),
                    employee_type=F('type'),  # Include type
                    department_name=F('department__department_name')  # Include department name
                )
                .annotate(
                    total_score=Value(0)  # Default score for those not in committees
                )
            )

            # Combine both groups
            combined_data = list(employees_in_committee) + list(employees_not_in_committee)

            # Filter by type if the query parameter is provided
            if emp_type is not None:
                combined_data = [
                    emp for emp in combined_data if str(emp['employee_type']) == emp_type
                ]

            # Sort by total_score based on the 'order' parameter (ascending or descending)
            reverse_sort = True if order == 'desc' else False
            combined_data = sorted(combined_data, key=lambda x: x['total_score'], reverse=reverse_sort)

            # Generate Excel file
            wb = Workbook()
            ws = wb.active
            ws.title = "Employee Report"

            # Add the header row
            ws.append([
                "Employee Name",
                "Department Name",
                "Total Score"
            ])

            # Add the employee data rows
            for emp in combined_data:
                ws.append([
                    emp['employee_name'],
                    emp['department_name'],
                    emp['total_score']
                ])

            # Create an in-memory file buffer
            response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            response['Content-Disposition'] = 'attachment; filename=employee_report.xlsx'
            
            # Save the workbook to the response
            wb.save(response)

            return response

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )





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