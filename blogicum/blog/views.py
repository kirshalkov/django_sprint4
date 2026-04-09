from django.shortcuts import get_object_or_404, redirect
from blog.models import Post, Category, Comment
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.urls import reverse_lazy
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, \
    UpdateView, CreateView, DeleteView
from django.db.models import Count
from .forms import PostForm, CustomUserChangeForm, CommentForm
from django.http import Http404
User = get_user_model()


class IndexView(ListView):
    model = Post
    template_name = 'blog/index.html'
    paginate_by = 10
    ordering = ['pub_date']

    def get_queryset(self):
        return Post.objects.filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True
        ).select_related(
            'category', 'location', 'author'
        ).annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date')


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_queryset(self):
        return Post.objects.select_related('category', 'location', 'author')

    def get_object(self, queryset=None):
        post = super().get_object(queryset)
        if not (post.is_published and 
                post.pub_date <= timezone.now() and 
                post.category.is_published):
            if self.request.user != post.author:
                raise Http404("Пост не найден")

        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comments.select_related(
            'author').all()
        context['form'] = CommentForm()
        return context


class CategoryPostsView(ListView):
    model = Post
    template_name = 'blog/category.html'
    paginate_by = 10

    def get_queryset(self):
        category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )
        return Post.objects.filter(
            category=category,
            is_published=True,
            pub_date__lte=timezone.now()
        ).order_by('-pub_date').select_related('category', 'location')


class ProfileView(DetailView):
    model = User
    template_name = 'blog/profile.html'

    def get_object(self, queryset=None):
        username = self.kwargs.get('username')
        return get_object_or_404(User, username=username)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile_user = self.get_object()
        posts = Post.objects.filter(
            author=profile_user
        ).select_related('category', 'location').annotate(
            comment_count=Count('comments')).order_by('-pub_date')
        paginator = Paginator(posts, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj
        context['profile'] = profile_user
        return context


class UserEditView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserChangeForm
    template_name = 'blog/user.html'
    form_class = CustomUserChangeForm

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy('blog:profile',
                            kwargs={'username': self.request.user.username})


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blog:profile', kwargs={
            'username': self.request.user.username})


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

    def handle_no_permission(self):
        post = self.get_object()
        return redirect('blog:post_detail', post_id=post.id)

    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={
            'post_id': self.object.id})


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'
    success_url = reverse_lazy('blog:index')

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.get_object())
        return context

class CommentAccessMixin(UserPassesTestMixin):
    def test_func(self):
        comment = self.get_object()
        return self.request.user == comment.author


class CommentPostMixin:
    def dispatch(self, request, *args, **kwargs):
        self.post_obj = get_object_or_404(Post, id=kwargs.get('post_id'))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post'] = self.post_obj
        return context


class CommentCreateView(LoginRequiredMixin, CommentPostMixin, CreateView):

    model = Comment
    form_class = CommentForm
    template_name = 'includes/comments.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.post_obj
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={
            'post_id': self.post_obj.id})


class CommentUpdateView(LoginRequiredMixin, CommentAccessMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'


    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={
            'post_id': self.object.post.id})


class CommentDeleteView(LoginRequiredMixin, CommentAccessMixin, DeleteView):

    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'


    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={
            'post_id': self.object.post.id})