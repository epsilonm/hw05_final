import uuid
from math import ceil

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.conf import settings

from posts.models import Post, Group

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testuser')
        cls.group = Group.objects.create(
            title='Test group',
            slug='test-group',
            description='About test group'
        )
        cls.urls = (
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': cls.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': cls.user.username}),
        )
        cls.PAGE_COUNT = 15

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)

    def test_paginator(self):
        """Check paginator contains right number of posts."""
        page_num = ceil(self.PAGE_COUNT / settings.POST_LIM)
        for _ in range(self.PAGE_COUNT):
            Post.objects.create(
                text=uuid.uuid4(),
                author=self.user,
                group=self.group,
            )

        for url in self.urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(len(response.context['page_obj']),
                                 settings.POST_LIM)
                response = self.authorized_client.get(
                    url + f'?page={page_num}')
                self.assertEqual(
                    len(response.context['page_obj']),
                    (self.PAGE_COUNT - ((page_num - 1) * settings.POST_LIM)))
