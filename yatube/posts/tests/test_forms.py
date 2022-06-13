import tempfile
import shutil

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Post, Group, Comment


User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testuser')
        cls.group = Group.objects.create(
            title='Test group',
            slug='test-group',
            description='About test group'
        )
        cls.second_group = Group.objects.create(
            title='Second test group',
            slug='test-group-second',
            description='About second test group'
        )
        cls.SMALL_GIF = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.SMALL_GIF_SECOND = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x01\x01\x01\x01\x01'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded_first = SimpleUploadedFile(
            name='small.gif',
            content=cls.SMALL_GIF,
            content_type='image/gif'
        )
        cls.uploaded_second = SimpleUploadedFile(
            name='small_2.gif',
            content=cls.SMALL_GIF_SECOND,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Test post',
            author=cls.user,
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Count Post objects after form validation."""
        post_count = Post.objects.count()
        form_data = {
            'text': 'Test post 2',
            'group': self.group.id,
            'image': self.uploaded_first
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username': self.user.username}))

        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=self.group.id,
                author=self.user,
                image='posts/small.gif'

            ).exists()
        )

    def test_edit_post(self):
        """Check changing post after editing."""
        second_form_data = {
            'text': 'Test post edited',
            'group': self.second_group.id,
            'image': self.uploaded_second
        }
        response = self.authorized_client.post(
            reverse(
                'posts:update_post',
                kwargs={'post_id': self.post.id},
            ),
            data=second_form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse(
                                 'posts:post_detail',
                                 kwargs={'post_id': self.post.id}
                             ))
        self.assertTrue(
            Post.objects.filter(
                text=second_form_data['text'],
                group=self.second_group.id,
                author=self.user,
                id=self.post.id,
                image='posts/small_2.gif'
            ).exists()
        )

    def test_add_comment(self):
        """Check adding comment on the post page."""
        form_data = {
            'text': 'Comment text'
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.id},
            ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse(
                                 'posts:post_detail',
                                 kwargs={'post_id': self.post.id}
                             ))
        self.assertTrue(
            Comment.objects.filter(
                text=form_data['text'],
                author=self.user,
                post=self.post
            ).exists()
        )
