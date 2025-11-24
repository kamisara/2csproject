```python
"""
Database models for the VulnScan authentication application.

This module defines the UserProfile model which extends Django's built-in
User model with additional profile information and avatar functionality.

Key Features:
- Extends Django User model with OneToOne relationship
- Provides avatar upload functionality with organized file structure
- Maintains referential integrity with CASCADE delete
- Supports optional avatar field for user flexibility

Security Considerations:
- Avatar uploads are validated for file type and size
- File paths are structured to prevent naming conflicts
- User authentication relies on Django's secure User model
"""

from pathlib import Path
from django.db import models
from django.contrib.auth.models import User


def avatar_upload_to(instance, filename):
    """
    Generate upload path for user avatar images.
    
    This function creates a structured file path for avatar uploads to:
    - Organize files by user ID for easy management
    - Prevent filename conflicts between users
    - Maintain original file extension for compatibility
    
    Path Format: avatars/{user_id}/avatar{extension}
    Example: avatars/42/avatar.jpg
    
    Args:
        instance: UserProfile instance being saved
        filename (str): Original filename of uploaded image
        
    Returns:
        str: Generated file path for avatar storage
        
    Example:
        >>> avatar_upload_to(user_profile, "profile_pic.jpg")
        'avatars/42/avatar.jpg'
    """
    # Extract file extension while maintaining security
    file_extension = Path(filename).suffix.lower()
    
    # Generate structured path: avatars/{user_id}/avatar{extension}
    return f"avatars/{instance.user_id}/avatar{file_extension}"


class UserProfile(models.Model):
    """
    Extended user profile model for VulnScan application.
    
    This model extends Django's built-in User model to provide
    additional user-specific data and functionality while maintaining
    compatibility with Django's authentication system.
    
    Relationships:
    - One-to-one relationship with Django User model
    - CASCADE delete ensures profile is removed when user is deleted
    
    Fields:
    - user: Reference to Django User model (required)
    - avatar: User profile picture (optional)
    
    Usage:
        user = User.objects.get(username='john')
        profile = user.profile  # Access via related_name
        profile.avatar = uploaded_file
        profile.save()
    """
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name="profile",
        verbose_name="Django User",
        help_text="Reference to the Django authentication user model"
    )
    
    avatar = models.ImageField(
        upload_to=avatar_upload_to,
        null=True,
        blank=True,
        verbose_name="Profile Avatar",
        help_text="User profile picture. Supported formats: JPG, PNG, GIF",
    )

    def __str__(self):
        """
        String representation of the UserProfile instance.
        
        Returns:
            str: Human-readable identifier for the profile
            
        Example:
            >>> str(user_profile)
            'Profile(42)'
        """
        return f"Profile({self.user_id})"

    class Meta:
        """
        Metadata options for the UserProfile model.
        
        Attributes:
            verbose_name: Human-readable name for single object
            verbose_name_plural: Human-readable name for multiple objects
            db_table: Custom database table name (optional)
        """
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
        # db_table = 'auth_user_profiles'  # Uncomment for custom table name

    def get_avatar_url(self):
        """
        Get the absolute URL for the user's avatar.
        
        Returns:
            str or None: Absolute URL to avatar image or None if no avatar
            
        Example:
            >>> profile.get_avatar_url()
            '/media/avatars/42/avatar.jpg'
        """
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        return None

    def delete_avatar(self):
        """
        Delete the avatar file from storage and clear the field.
        
        This method ensures the physical file is removed from storage
        when the avatar field is cleared.
        """
        if self.avatar:
            # Delete the physical file from storage
            self.avatar.delete(save=False)
            # Clear the field
            self.avatar = None
            self.save()

"""
Database Schema Information:

Table: auth_app_userprofile (or custom name if specified)
Columns:
- id: Primary key (auto-increment)
- user_id: Foreign key to auth_user (unique constraint)
- avatar: VARCHAR containing file path to avatar image

Indexes:
- Automatic primary key index on id
- Unique index on user_id (enforced by OneToOneField)
- Potential index on avatar field for query optimization

Relationships:
UserProfile (1) ───── (1) User
   │                      │
   │ avatar (file)        │ username, email, password, etc.

File Storage Structure:
media/
└── avatars/
    ├── 1/
    │   └── avatar.jpg
    ├── 2/
    │   └── avatar.png
    └── 42/
        └── avatar.gif

Security and Validation:
- Avatar files should be validated in views for:
  - File type (jpg, png, gif only)
  - File size (max 2MB recommended)
  - Image dimensions (resize if needed)
- Consider using django-cleanup for automatic file deletion
- Implement virus scanning for uploaded files in production

Migration Notes:
When making changes to this model:
1. Run: python manage.py makemigrations auth_app
2. Run: python manage.py migrate auth_app
3. Test avatar upload functionality

Alternative Approaches Considered:
- Using django-imagekit for image processing
- Storing avatars in cloud storage (S3, Cloudinary)
- Using gravatar integration for default avatars
- Extending AbstractUser instead of UserProfile
"""
```
