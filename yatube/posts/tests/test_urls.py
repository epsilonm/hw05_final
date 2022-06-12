from http import HTTPStatus

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.cache import cache

from ..models import Group, Post

User = get_user_model()


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.another_user = User.objects.create_user(username='another')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.URLS = {
            '/': reverse('posts:index'),
            f'/group/{cls.group.slug}/': reverse(
                'posts:group_list', kwargs={'slug': cls.group.slug}),
            f'/profile/{cls.user.username}/': reverse(
                'posts:profile', kwargs={'username': cls.user.username}),
            f'/posts/{cls.post.id}/': reverse(
                'posts:post_detail', kwargs={'post_id': cls.post.id}),
            '/create/': reverse('posts:post_create'),
            f'/posts/{cls.post.id}/edit/': reverse(
                'posts:update_post', kwargs={'post_id': cls.post.id}),
            '/posts/345/': reverse(
                'posts:post_detail', kwargs={'post_id': 345}),
        }
        cls.template_urls = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': cls.group.slug}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': cls.user.username}):
                'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': cls.post.id}):
                'posts/post_detail.html',
            reverse('posts:update_post',
                    kwargs={'post_id': cls.post.id}):
                'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_detail', kwargs={'post_id': 345}):
                'core/404.html'
        }
        cls.urls_statuses = (
            (reverse('posts:index'), False, HTTPStatus.OK,),
            (reverse('posts:group_list', kwargs={'slug': cls.group.slug}),
             False, HTTPStatus.OK,),
            (reverse('posts:profile', kwargs={'username': cls.user.username}),
             False, HTTPStatus.OK,),
            (reverse('posts:post_detail',
                     kwargs={'post_id': cls.post.id}),
             False, HTTPStatus.OK,),
            (reverse('posts:update_post',
                     kwargs={'post_id': cls.post.id}),
             True, HTTPStatus.OK,),
            (reverse('posts:post_create'), True, HTTPStatus.OK,),
            (reverse('posts:post_detail', kwargs={'post_id': 345}),
             False, HTTPStatus.NOT_FOUND),
        )

    def setUp(self):
        # Guest client
        self.guest_client = Client()
        # User client
        self.authorised_client = Client()
        self.authorised_client.force_login(self.user)

    def tearDown(self) -> None:
        cache.clear()

    def test_named_url_pattern_equals_url_route(self):
        """Check named URL pattern equals URL route."""
        for route, named_url in self.URLS.items():
            with self.subTest(route=route):
                self.assertEqual(route, named_url)

    def test_urls_exist_at_desired_location(self):
        """Check access to URL and HTTPStatus code."""
        for address, need_auth, status in self.urls_statuses:
            with self.subTest(address=address):
                if not need_auth:
                    response = self.guest_client.get(address)
                else:
                    response = self.authorised_client.get(address)
                self.assertEqual(response.status_code, status)

    def test_urls_uses_correct_template(self):
        """URL-address uses correct template."""
        for address, template in self.template_urls.items():
            with self.subTest(address=address):
                response = self.authorised_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_post_edit_redirects_non_author(self):
        """Page 'posts/<int:post_id>/edit/'
         redirects non-author user."""
        self.authorised_client.force_login(self.another_user)
        response = self.authorised_client.get(
            reverse('posts:update_post', kwargs={'post_id': self.post.id}))
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))

    def test_post_create_redirect_anonymous(self):
        """Page /create/ redirects anonymous user."""
        url = reverse('posts:post_create')
        response = self.guest_client.get(url)
        self.assertRedirects(
            response, reverse('users:login') + f'?next={url}')

    def test_add_comment_redirect_anonymous(self):
        url = reverse('posts:add_comment', kwargs={'post_id': self.post.id})
        response = self.guest_client.get(url)
        self.assertRedirects(
            response, reverse('users:login') + f'?next={url}'
        )
