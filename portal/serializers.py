from rest_framework import serializers
from .models import Ticket, Attachment, TicketAttachment, Comment, CommentMention


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ['id', 'file_name', 'file_type', 'file_path', 'tenant_id', 'metadata', 'created_at']
        read_only_fields = ['id', 'tenant_id', 'created_at']


class TicketAttachmentSerializer(serializers.ModelSerializer):
    attachment = AttachmentSerializer(read_only=True, source='attachment_obj')

    class Meta:
        model = TicketAttachment
        fields = ['id', 'reference_id', 'attachment_id', 'created_at']
        read_only_fields = ['id', 'created_at']


class TicketSerializer(serializers.ModelSerializer):
    attachments = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            'id', 'title', 'description', 'category', 'status', 'priority',
            'tenant_id', 'created_by', 'assigned_to', 'due_date', 'resolved_at', 'closed_at',
            'comments', 'attachments', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'status', 'tenant_id', 'created_at', 'updated_at']

    def get_attachments(self, obj):
        attachment_ids = TicketAttachment.objects.filter(
            reference_id=obj.id
        ).values_list('attachment_id', flat=True)
        attachments = Attachment.objects.filter(id__in=attachment_ids)
        return AttachmentSerializer(attachments, many=True).data


class TicketCreateSerializer(serializers.ModelSerializer):
    # List of existing attachment IDs to link after ticket creation
    attachment_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, write_only=True
    )

    class Meta:
        model = Ticket
        fields = [
            'title', 'description', 'category', 'priority',
            'created_by', 'due_date', 'comments', 'attachment_ids',
        ]

    def create(self, validated_data):
        attachment_ids = validated_data.pop('attachment_ids', [])
        ticket = Ticket.objects.create(**validated_data)
        for attachment_id in attachment_ids:
            TicketAttachment.objects.create(reference_id=ticket.id, attachment_id=attachment_id)
        return ticket


class TicketUpdateSerializer(serializers.ModelSerializer):
    # New attachment IDs to append to the ticket
    attachment_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, write_only=True
    )

    class Meta:
        model = Ticket
        fields = [
            'title', 'description', 'category', 'status', 'priority',
            'assigned_to', 'due_date', 'resolved_at', 'closed_at',
            'comments', 'attachment_ids',
        ]

    def update(self, instance, validated_data):
        attachment_ids = validated_data.pop('attachment_ids', [])
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        for attachment_id in attachment_ids:
            TicketAttachment.objects.get_or_create(
                reference_id=instance.id, attachment_id=attachment_id
            )
        return instance


class CommentMentionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentMention
        fields = ['id', 'comment_id', 'mentioned_user_id', 'created_at']


class CommentSerializer(serializers.ModelSerializer):
    attachments = serializers.SerializerMethodField()
    mentions = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id', 'ticket_id', 'tenant_id', 'user_id', 'parent_id', 'message',
            'is_deleted', 'attachments', 'mentions', 'created_at', 'updated_at',
        ]

    def get_attachments(self, obj):
        attachment_ids = TicketAttachment.objects.filter(
            reference_id=obj.id
        ).values_list('attachment_id', flat=True)
        attachments = Attachment.objects.filter(id__in=attachment_ids)
        return AttachmentSerializer(attachments, many=True).data

    def get_mentions(self, obj):
        mentions = CommentMention.objects.filter(comment_id=obj.id)
        return CommentMentionSerializer(mentions, many=True).data


class CommentCreateSerializer(serializers.ModelSerializer):
    attachment_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, write_only=True
    )
    mentioned_user_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, write_only=True
    )

    class Meta:
        model = Comment
        fields = ['ticket_id', 'user_id', 'parent_id', 'message', 'attachment_ids', 'mentioned_user_ids']

    def validate_parent_id(self, value):
        if value is not None and not Comment.objects.filter(id=value, is_deleted=False).exists():
            raise serializers.ValidationError('Parent comment does not exist.')
        return value

    def create(self, validated_data):
        attachment_ids = validated_data.pop('attachment_ids', [])
        mentioned_user_ids = validated_data.pop('mentioned_user_ids', [])
        comment = Comment.objects.create(**validated_data)
        for attachment_id in attachment_ids:
            TicketAttachment.objects.get_or_create(
                reference_id=comment.id, attachment_id=attachment_id
            )
        for user_id in mentioned_user_ids:
            CommentMention.objects.create(comment_id=comment.id, mentioned_user_id=user_id)
        return comment


class CommentUpdateSerializer(serializers.ModelSerializer):
    attachment_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, write_only=True
    )
    mentioned_user_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, write_only=True
    )

    class Meta:
        model = Comment
        fields = ['message', 'attachment_ids', 'mentioned_user_ids']

    def update(self, instance, validated_data):
        attachment_ids = validated_data.pop('attachment_ids', [])
        mentioned_user_ids = validated_data.pop('mentioned_user_ids', [])
        instance.message = validated_data.get('message', instance.message)
        instance.save()
        for attachment_id in attachment_ids:
            TicketAttachment.objects.get_or_create(
                reference_id=instance.id, attachment_id=attachment_id
            )
        for user_id in mentioned_user_ids:
            CommentMention.objects.get_or_create(
                comment_id=instance.id, mentioned_user_id=user_id
            )
        return instance

