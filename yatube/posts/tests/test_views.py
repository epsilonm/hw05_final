import tempfile
import shutil

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.core.cache import cache

from posts.models import Post, Group, Follow
from posts.forms import PostForm

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.user_without_follow = User.objects.create_user(username='hikki')
        cls.user = User.objects.create_user(username='user')
        cls.group = Group.objects.create(
            title='Test group',
            slug='test-group',
            description='About test group'
        )
        cls.another_group = Group.objects.create(
            title='Test group 2',
            slug='test-group-2',
            description='About test group 2'
        )
        cls.SMALL_GIF = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.SMALL_GIF,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Text',
            author=cls.author,
            group=cls.group,
            image=cls.uploaded
        )
        cls.post_two = Post.objects.create(
            text='Text',
            author=cls.author,
            group=cls.group,
            image=cls.uploaded
        )
        cls.another_group_post = Post.objects.create(
            text='Text',
            author=cls.author,
            group=cls.another_group
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.author)

    def tearDown(self) -> None:
        cache.clear()

    def test_post_have_been_added_to_context(self):
        """Check that post was successfully added to context."""
        urls = (
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': self.author.username}),
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertIn(self.post, response.context['page_obj'])

    def test_pages_have_correct_context(self):
        """Check that posts:index, posts:group_list, posts:profile
        context has correct objects within."""
        urls_contexts_objects = (
            (reverse('posts:group_list',
                     kwargs={'slug': self.group.slug}),
             'group', self.group),
            (reverse('posts:profile',
                     kwargs={'username': self.author.username}),
             'author', self.author),
            (reverse('posts:post_detail',
                     kwargs={'post_id': self.post.id}),
             'post', self.post),
        )
        for url, context, object in urls_contexts_objects:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.context.get(context), object)

    def test_post_create_show_correct_context(self):
        """Post_create template was formed correctly."""
        response = self.authorized_client.get(
            reverse('posts:post_create')
        )
        self.assertIsInstance(response.context.get('form'), PostForm)

    def test_update_post_show_correct_context(self):
        """Update_post has correct values within form fields."""
        response = self.authorized_client.get(
            reverse('posts:update_post', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(response.context.get('form').instance, self.post)

    def test_another_group_post_does_not_maps_in_group_list(self):
        """Check that post with group does not maps in another group list."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        self.assertNotIn(self.another_group_post, response.context['page_obj'])

    def test_index_cache(self):
        """Check that @cache_page works correctly."""
        response = self.authorized_client.get(reverse('posts:index'))
        temp = response.content
        self.post_two.delete()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(temp, response.content)
        cache.clear()
        self.assertEqual(temp, response.content)
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(temp, response.content)

    def test_profile_follow_and_unfollow(self):
        """Check that profile_follow works correctly."""
        self.authorized_client.force_login(self.user)
        self.authorized_client.post(
            reverse('posts:profile_follow',
                    kwargs={'username': self.author.username})
        )
        self.assertTrue(
            Follow.objects.filter(user=self.user, author=self.author).exists()
        )

    def test_profile_unfollow(self):
        """Check that profile_unfollow works correctly."""
        self.authorized_client.force_login(self.user)
        Follow.objects.create(user=self.user, author=self.author)
        self.authorized_client.post(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.author.username})
        )
        self.assertFalse(
            Follow.objects.filter(user=self.user, author=self.author).exists()
        )

    def test_follow_index_works_correctly(self):
        """Check that following author appears in follow_index if user is follower
         and not appears if user is not follower.
         """
        self.authorized_client.force_login(self.user)
        Follow.objects.create(user=self.user, author=self.author)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertIn(self.post, response.context['page_obj'])
        self.authorized_client.force_login(self.user_without_follow)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotIn(self.post, response.context['page_obj'])
