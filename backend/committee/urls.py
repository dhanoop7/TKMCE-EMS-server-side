from django.urls import path
from .views import CreateCommittee, ListCommittees, CommitteeDetailView, generate_committee_report

urlpatterns = [
    path('create-committee/', CreateCommittee.as_view(), name='create_committee'),
    path('committees/', ListCommittees.as_view(), name='list_committees'),
    path('committee-detail/<int:pk>/', CommitteeDetailView.as_view(), name='committee-detail'),
    path('report/<int:committee_id>/', generate_committee_report, name='committee_report'),

]