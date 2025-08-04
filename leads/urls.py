
from django.urls import path
from .views import (
    LeadListView, LeadDetailView, LeadCreateView, LeadUpdateView, LeadDeleteView,
    AssignAgentView, CategoryListView, CategoryDetailView, LeadCategoryUpdateView,
    LeadInteractionCreateView, FollowUpScheduleView, LeadSnoozeView, LeadUnSnoozeView,
    LeadScoringView, KanbanBoardView, AgentPerformanceView, SourceHeatmapView,
    MLModelTrainingView
)

app_name = "leads"

urlpatterns = [
    path('', LeadListView.as_view(), name='lead-list'),
    path('<int:pk>/', LeadDetailView.as_view(), name='lead-detail'),
    path('<int:pk>/update/', LeadUpdateView.as_view(), name='lead-update'),
    path('<int:pk>/delete/', LeadDeleteView.as_view(), name='lead-delete'),
    path('<int:pk>/assign-agent/', AssignAgentView.as_view(), name='assign-agent'),
    path('<int:pk>/category/', LeadCategoryUpdateView.as_view(), name='lead-category-update'),
    path('<int:lead_id>/interaction/', LeadInteractionCreateView.as_view(), name='lead-interaction-create'),
    path('<int:lead_id>/follow-up/', FollowUpScheduleView.as_view(), name='follow-up-schedule'),
    path('<int:lead_id>/snooze/', LeadSnoozeView.as_view(), name='lead-snooze'),
    path('<int:lead_id>/unsnooze/', LeadUnSnoozeView.as_view(), name='lead-unsnooze'),
    path('<int:lead_id>/scoring/', LeadScoringView.as_view(), name='lead-scoring'),
    path('create/', LeadCreateView.as_view(), name='lead-create'),
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('categories/<int:pk>/', CategoryDetailView.as_view(), name='category-detail'),
    path('kanban/', KanbanBoardView.as_view(), name='kanban-board'),
    path('performance/', AgentPerformanceView.as_view(), name='agent-performance'),
    path('source-heatmap/', SourceHeatmapView.as_view(), name='source-heatmap'),
    path('train-ml-model/', MLModelTrainingView.as_view(), name='train-ml-model'),
]