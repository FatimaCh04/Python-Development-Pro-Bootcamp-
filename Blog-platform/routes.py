import os
import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

from models import db, User, Post, Category, Tag, Comment
from forms import RegistrationForm, LoginForm, UpdateProfileForm, PostForm, CommentForm, SearchForm

bp = Blueprint('main', __name__)


def save_upload_file(file_obj):
    """Utility to save uploaded files with a unique filename."""
    if not file_obj or not file_obj.filename:
        return None
    random_hex = uuid.uuid4().hex[:10]
    filename = secure_filename(file_obj.filename)
    _, ext = os.path.splitext(filename)
    unique_filename = f"{random_hex}{ext.lower()}"
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
    file_obj.save(filepath)
    return unique_filename


# --- Context Processor ---
@bp.app_context_processor
def inject_globals():
    """Inject search form and categories globally into all templates."""
    search_form = SearchForm()
    categories = Category.query.order_by(Category.name.asc()).all()
    recent_posts = Post.query.filter_by(is_published=True).order_by(Post.created_at.desc()).limit(5).all()
    return dict(
        search_form=search_form,
        global_categories=categories,
        global_recent_posts=recent_posts
    )


# --- Public Routes ---
@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('q', '').strip()
    category_slug = request.args.get('category', '').strip()
    tag_slug = request.args.get('tag', '').strip()

    query = Post.query.filter_by(is_published=True)

    selected_category = None
    if category_slug:
        selected_category = Category.query.filter_by(slug=category_slug).first_or_404()
        query = query.filter_by(category_id=selected_category.id)

    selected_tag = None
    if tag_slug:
        selected_tag = Tag.query.filter_by(slug=tag_slug).first_or_404()
        query = query.filter(Post.tags.contains(selected_tag))

    if search_query:
        search_pattern = f"%{search_query}%"
        query = query.filter(
            (Post.title.ilike(search_pattern)) |
            (Post.summary.ilike(search_pattern)) |
            (Post.content.ilike(search_pattern))
        )

    pagination = query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False
    )
    posts = pagination.items

    featured_post = None
    if page == 1 and not search_query and not category_slug and not tag_slug and posts:
        featured_post = posts[0]

    return render_template(
        'index.html',
        posts=posts,
        pagination=pagination,
        featured_post=featured_post,
        search_query=search_query,
        selected_category=selected_category,
        selected_tag=selected_tag
    )


@bp.route('/post/<slug>', methods=['GET', 'POST'])
def post_detail(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()
    
    if request.method == 'GET':
        post.views += 1
        db.session.commit()

    comment_form = CommentForm()
    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('You need to log in to leave a comment.', 'warning')
            return redirect(url_for('main.login', next=request.url))
        
        comment = Comment(
            content=comment_form.content.data.strip(),
            post_id=post.id,
            user_id=current_user.id
        )
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been published!', 'success')
        return redirect(url_for('main.post_detail', slug=post.slug) + '#comments')

    comments = post.comments.order_by(Comment.created_at.desc()).all()
    return render_template('post.html', post=post, comment_form=comment_form, comments=comments)


@bp.route('/category/<slug>')
def category_posts(slug):
    return redirect(url_for('main.index', category=slug))


@bp.route('/tag/<slug>')
def tag_posts(slug):
    return redirect(url_for('main.index', tag=slug))


# --- Authentication Routes ---
@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data.strip(),
            email=form.email.data.strip().lower()
        )
        user.set_password(form.password.data)
        
        if User.query.count() == 0:
            user.is_admin = True

        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash('Account created successfully! Welcome to the platform.', 'success')
        return redirect(url_for('main.dashboard'))
        
    return render_template('register.html', form=form)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
            
    return render_template('login.html', form=form)


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UpdateProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.username = form.username.data.strip()
        current_user.email = form.email.data.strip().lower()
        current_user.bio = form.bio.data.strip() if form.bio.data else ''
        
        if form.avatar.data:
            avatar_filename = save_upload_file(form.avatar.data)
            if avatar_filename:
                current_user.avatar = avatar_filename

        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('main.profile'))
        
    return render_template('profile.html', form=form)


# --- Dashboard & Author Post CRUD Routes ---
@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        user_posts = Post.query.order_by(Post.created_at.desc()).all()
    else:
        user_posts = current_user.posts.order_by(Post.created_at.desc()).all()

    published_count = sum(1 for p in user_posts if p.is_published)
    draft_count = sum(1 for p in user_posts if not p.is_published)
    total_views = sum(p.views for p in user_posts)
    total_comments = sum(p.comments.count() for p in user_posts)

    return render_template(
        'dashboard.html',
        posts=user_posts,
        published_count=published_count,
        draft_count=draft_count,
        total_views=total_views,
        total_comments=total_comments
    )


@bp.route('/post/new', methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()
    
    categories = Category.query.order_by(Category.name.asc()).all()
    form.category_id.choices = [(0, 'Select Category (Optional)')] + [(c.id, c.name) for c in categories]

    if form.validate_on_submit():
        base_slug = Post.generate_slug(form.title.data)
        slug = base_slug
        count = 1
        while Post.query.filter_by(slug=slug).first() is not None:
            slug = f"{base_slug}-{count}"
            count += 1

        image_filename = None
        if form.featured_image.data:
            image_filename = save_upload_file(form.featured_image.data)

        category_id = form.category_id.data if form.category_id.data != 0 else None

        post = Post(
            title=form.title.data.strip(),
            slug=slug,
            summary=form.summary.data.strip(),
            content=form.content.data.strip(),
            featured_image=image_filename,
            is_published=(form.status.data == 'published'),
            category_id=category_id,
            author=current_user
        )

        if form.tags.data:
            tag_names = [t.strip() for t in form.tags.data.split(',') if t.strip()]
            for name in tag_names:
                tag_slug = Tag.generate_slug(name)
                tag = Tag.query.filter_by(slug=tag_slug).first()
                if not tag:
                    tag = Tag(name=name, slug=tag_slug)
                    db.session.add(tag)
                post.tags.append(tag)

        db.session.add(post)
        db.session.commit()
        
        status_msg = 'published' if post.is_published else 'saved as a draft'
        flash(f'Post successfully {status_msg}!', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('create_post.html', form=form, title="Create New Post")


@bp.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user and not current_user.is_admin:
        abort(403)

    form = PostForm()
    categories = Category.query.order_by(Category.name.asc()).all()
    form.category_id.choices = [(0, 'Select Category (Optional)')] + [(c.id, c.name) for c in categories]

    if form.validate_on_submit():
        post.title = form.title.data.strip()
        post.summary = form.summary.data.strip()
        post.content = form.content.data.strip()
        post.category_id = form.category_id.data if form.category_id.data != 0 else None
        post.is_published = (form.status.data == 'published')

        if form.featured_image.data:
            image_filename = save_upload_file(form.featured_image.data)
            if image_filename:
                post.featured_image = image_filename

        post.tags.clear()
        if form.tags.data:
            tag_names = [t.strip() for t in form.tags.data.split(',') if t.strip()]
            for name in tag_names:
                tag_slug = Tag.generate_slug(name)
                tag = Tag.query.filter_by(slug=tag_slug).first()
                if not tag:
                    tag = Tag(name=name, slug=tag_slug)
                    db.session.add(tag)
                post.tags.append(tag)

        db.session.commit()
        flash('Post updated successfully!', 'success')
        return redirect(url_for('main.dashboard'))

    elif request.method == 'GET':
        form.title.data = post.title
        form.summary.data = post.summary
        form.content.data = post.content
        form.category_id.data = post.category_id if post.category_id else 0
        form.status.data = 'published' if post.is_published else 'draft'
        form.tags.data = ', '.join([t.name for t in post.tags])

    return render_template('edit_post.html', form=form, title="Edit Post", post=post)


@bp.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user and not current_user.is_admin:
        abort(403)
        
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted successfully.', 'info')
    return redirect(url_for('main.dashboard'))


@bp.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.author != current_user and comment.post.author != current_user and not current_user.is_admin:
        abort(403)
        
    post_slug = comment.post.slug
    db.session.delete(comment)
    db.session.commit()
    flash('Comment removed.', 'info')
    return redirect(url_for('main.post_detail', slug=post_slug) + '#comments')


# --- Error Handlers ---
@bp.app_errorhandler(403)
def forbidden_error(error):
    return render_template('403.html'), 403


@bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
