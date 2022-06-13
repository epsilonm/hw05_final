from django.conf import settings
from django.shortcuts import get_object_or_404, render, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from posts.models import Post, Group, User, Comment, Follow
from posts.forms import PostForm, CommentForm


def get_page_obj(page_number, posts, limit):
    paginator = Paginator(posts, limit)
    return paginator.get_page(page_number)


@cache_page(20, key_prefix='index_page')
def index(request):
    """Represents index.html"""
    template = 'posts/index.html'
    posts = Post.objects.select_related('author', 'group')
    page_obj = get_page_obj(request.GET.get('page'),
                            posts, settings.POST_LIM)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    """Represents group/<slug>"""
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author')
    page_obj = get_page_obj(request.GET.get('page'), posts, settings.POST_LIM)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    """Represents author profile with all posts and number of posts"""
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    posts = author.posts.select_related('group')
    page_obj = get_page_obj(request.GET.get('page'),
                            posts, settings.POST_LIM)
    following = False
    if request.user.is_authenticated:
        if request.user != author:
            following = Follow.objects.filter(user=request.user).exists()
    context = {
        'page_obj': page_obj,
        'author': author,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    """Represents post with information about author and group"""
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post.objects.select_related('author',
                                                         'group'),
                             pk=post_id)
    form = CommentForm(
        request.POST or None
    )
    comments = Comment.objects.filter(post=post)
    context = {
        'post': post,
        'form': form,
        'comments': comments
    }
    return render(request, template, context)


@login_required
def post_create(request):
    """Creating post function. After post created
     redirects to author profile."""
    template = 'posts/create_post.html'
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', post.author.username)
    return render(request, template, {'form': form})


def post_edit(request, post_id):
    """Updating post function. After successful update
    redirects to post_detail page"""
    template = 'posts/create_post.html'
    post = get_object_or_404(Post.objects.select_related('author',
                                                         'group'),
                             pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(request.POST or None,
                    instance=post,
                    files=request.FILES or None,)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    return render(request,
                  template,
                  {'form': form, 'is_edit': True}
                  )


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post.objects.select_related('author',
                                                         'group'),
                             pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    followers = Follow.objects.select_related(
        "user").select_related(
        "author").filter(user=request.user)
    posts = Post.objects.select_related(
        "author").select_related(
        "group").filter(
        author__in=followers.values("author")
    )
    page_obj = get_page_obj(request.GET.get('page'),
                            posts, settings.POST_LIM)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author and not Follow.objects.filter(
            user=request.user, author=author).exists():
        Follow.objects.create(
            user=request.user, author=author)
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    unfollow = request.user.follower.get(author=author)
    unfollow.delete()
    return redirect('posts:follow_index')