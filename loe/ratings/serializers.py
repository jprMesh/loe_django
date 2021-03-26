from django.contrib.auth import get_user_model
from rest_framework import serializers
from ratings.models import Prediction


class PredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prediction
        fields = ['username', 'match', 'predicted_t1_win_prob']
