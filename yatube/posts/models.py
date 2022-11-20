from django.db import models
from django.contrib.auth import get_user_model
from pytils.translit import slugify

User = get_user_model()


class Group(models.Model):
    """Grop model"""
    title = models.CharField(max_length=200,
                             verbose_name='Title',
                             help_text='Max 200 characters')
    slug = models.SlugField(unique=True,
                            verbose_name='Group',
                            help_text='Enter group URL')
    description = models.TextField(verbose_name='Description',
                                   help_text='Describe your group')

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:100]
        super().save(*args, **kwargs)


class Post(models.Model):
    """Post model"""
    text = models.TextField(verbose_name='Text',
                            help_text='Enter text of your post')
    pub_date = models.DateTimeField(auto_now_add=True,
                                    verbose_name='Publication date',
                                    db_index=True)
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='posts',
                               verbose_name='User name',
                               help_text='Enter username'
                               )
    group = models.ForeignKey(Group,
                              blank=True,
                              null=True,
                              on_delete=models.SET_NULL,
                              verbose_name='Group name',
                              help_text='Enter the name of group',
                              related_name='posts'
                              )
    image = models.ImageField(
        'Image',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(Post,
                             related_name='comments',
                             on_delete=models.CASCADE,
                             verbose_name='Comment')
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='comments',
                               verbose_name='Commentator name'
                               )
    text = models.TextField(verbose_name='Text',
                            help_text='Enter text of your comment')
    created = models.DateTimeField(auto_now_add=True,
                                   verbose_name='Publication date')


class Follow(models.Model):
    user = models.ForeignKey(User,
                             related_name='follower',
                             verbose_name='Follower',
                             on_delete=models.CASCADE)
    author = models.ForeignKey(User,
                               related_name='following',
                               verbose_name='Author',
                               on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'user'],
                name='unique_following'
            ),
            models.CheckConstraint(check=~models.Q(user=models.F('author')),
                                   name='check_following')
        ]

    def __str__(self):
        return f'User {self.user} has followed on {self.author}'
