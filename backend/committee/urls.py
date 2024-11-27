from django.urls import path
from .views import (CreateCommittee, 
                    ListCommittees, 
                    CommitteeDetailView, 
                    generate_committee_report,
                    # generate_committee_word, 
                    AddMainCommitteeMembers, 
                    SubCommitteeCreateView, 
                    AddSubcommitteeMemberView, 
                    EditCommittee, 
                    DeleteSubcommitteeMemberView, 
                    EditSubCommitteeView,
                    SubCommitteeRetrieveView,
                    DeleteCommittee,)

urlpatterns = [
    path('create-committee/', CreateCommittee.as_view(), name='create_committee'),
    path('committees/', ListCommittees.as_view(), name='list_committees'),
    path('add-main-committee-members/', AddMainCommitteeMembers.as_view(), name='add-main-committee-members'),
    path('committee/<int:committee_id>/subcommittee/', SubCommitteeCreateView.as_view(), name='add_sub_committee'),
    path('subcommittee/<int:subcommittee_id>/add-members/', AddSubcommitteeMemberView.as_view(), name='add-subcommittee-member'),
    path('committee-detail/<int:pk>/', CommitteeDetailView.as_view(), name='committee-detail'),
    path('report/<int:committee_id>/', generate_committee_report, name='committee_report'),
    # path('report-word/<int:committee_id>/', generate_committee_word, name='committee_report_word'),
    path('edit/<int:committee_id>/', EditCommittee.as_view(), name='edit-committee'),
    path('committee-detail/<int:id>/delete/', AddMainCommitteeMembers.as_view(), name='committee-detail-delete'),
    path('delete-committee/<int:committee_id>/', DeleteCommittee.as_view(), name='delete_committee'),
    path('delete-subcommittee-member/<int:subcommittee_id>/member/<int:member_id>/', DeleteSubcommitteeMemberView.as_view(),name='delete_subcommittee_member'),
    path('edit-subcommittee/<int:subcommittee_id>/', EditSubCommitteeView.as_view(), name='edit-subcommittee'),
    path('single-subcommittee/<int:committee_id>/subcommittee/<int:subcommittee_id>/', SubCommitteeRetrieveView.as_view(), name='get_subcommittee'),

]