from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from api.models.techniques import Technique
from api.models.votes import TechniqueVote
from api.serializers.techniques import TechniqueSerializer
from api.permissions import IsTechniquesAuthenticated, IsNotSeller


class TechniqueViewSet(ModelViewSet):
    queryset = Technique.objects.all()
    serializer_class = TechniqueSerializer

    def get_permissions(self):
        return [IsNotSeller(), IsTechniquesAuthenticated()]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_destroy(self, instance):
        user = self.request.user
        if user != instance.created_by and not user.is_staff:
            raise PermissionError("Not authorized to delete this technique.")
        instance.delete()


class TechniqueVoteView(APIView):
    permission_classes = [IsAuthenticated, IsNotSeller]

    def post(self, request, technique_id):
        vote = request.data.get('vote')

        if vote not in ['APPROVE', 'REJECT']:
            return Response({"error": "Invalid vote. Use 'APPROVE' or 'REJECT'."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            technique = Technique.objects.get(id=technique_id)
        except Technique.DoesNotExist:
            return Response({"error": "Technique not found."}, status=status.HTTP_404_NOT_FOUND)

        if TechniqueVote.objects.filter(user=request.user, technique=technique).exists():
            return Response({"error": "You have already voted on this technique."}, status=status.HTTP_400_BAD_REQUEST)

        TechniqueVote.objects.create(user=request.user, technique=technique, vote=vote)

        if vote == 'APPROVE':
            technique.approval_votes += 1
        else:
            technique.rejection_votes += 1

        technique.save()
        technique.evaluate()

        return Response({"technique_status": technique.status}, status=status.HTTP_200_OK)
