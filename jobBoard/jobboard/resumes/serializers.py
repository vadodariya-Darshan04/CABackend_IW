from rest_framework import serializers
from .models import Resume


class ResumeSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()

    class Meta:
        model = Resume
        fields = ['id', 'title', 'file', 'file_url', 'file_name', 'is_default', 'uploaded_at', 'updated_at']
        read_only_fields = ['uploaded_at', 'updated_at']
        extra_kwargs = {'file': {'write_only': True}}

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None

    def get_file_name(self, obj):
        if obj.file:
            return obj.file.name.split('/')[-1]
        return None

    def validate_file(self, value):
        # Max 5MB
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError('Resume file must be under 5MB.')
        # Allow PDF, DOC, DOCX
        allowed = ['application/pdf',
                   'application/msword',
                   'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
        if value.content_type not in allowed:
            raise serializers.ValidationError('Only PDF, DOC, DOCX files are allowed.')
        return value
