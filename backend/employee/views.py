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





class AvailableEmployeeListView(APIView):
    
    def get(self, request, *args, **kwargs):
        # Get the parameters from the request
        department = request.GET.get('department')
        emp_type = request.GET.get('type')

        # Start with the initial queryset, which defaults to all employees
        queryset = Employee.objects.all()

        # If department is provided and is not empty, filter by department
        if department:
            queryset = queryset.filter(department_id=department)

        # If emp_type is provided and is valid (numeric), filter by emp_type
        if emp_type and emp_type.isdigit():
            queryset = queryset.filter(type=int(emp_type))

        # Serialize the queryset
        serializer = EmployeefilterSerializers(queryset, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
#view to add filtering options this view will also exclude employees on leave
    

class EmployeeScoresView(APIView):
    def get(self, request):
        
        employee_scores = (
            CommitteeDetails.objects
            .filter(committee_id__is_active=True)
            .values('employee_id')
            .annotate(total_score=Sum('score'))
            .order_by('total_score')  # Ascending order by score
        )

        # Fetching employee details along with scores
        response_data = [
            {
                'employee_id': emp_score['employee_id'],
                'employee_name': Employee.objects.get(id=emp_score['employee_id']).name,  # Assuming Employee has a 'name' field
                'total_score': emp_score['total_score']
            }
            for emp_score in employee_scores
        ]

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