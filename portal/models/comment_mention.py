from django.db import models


class CommentMention(models.Model):
    id = models.BigAutoField(primary_key=True)
    comment_id = models.BigIntegerField()
    mentioned_user_id = models.BigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Mention(comment={self.comment_id}, user={self.mentioned_user_id})"

    class Meta:
        db_table = 'portal_comment_mention'
        ordering = ['-created_at']
