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
    """
    # Extract file extension from original filename
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
    """
    
    # One-to-one relationship with Django User model
    # CASCADE delete: profile is deleted when user is deleted
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    
    # User profile picture - optional field with custom upload path
    # Supports common image formats (validated in views)
    avatar = models.ImageField(upload_to=avatar_upload_to, null=True, blank=True)

    def __str__(self):
        """
        String representation of the UserProfile instance.
        
        Returns:
            str: Human-readable identifier for the profile
        """
        return f"Profile({self.user_id})"

    class Meta:
        """
        Metadata options for the UserProfile model.
        """
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def get_avatar_url(self):
        """
        Get the absolute URL for the user's avatar.
        
        Returns:
            str or None: Absolute URL to avatar image or None if no avatar
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

Table Structure:
- id: Primary key (auto-increment)
- user_id: Foreign key to auth_user (unique constraint)
- avatar: VARCHAR containing file path to avatar image

Relationships:
UserProfile (1) ───── (1) User
   │
   └── avatar (ImageField)

File Storage Structure:
media/
└── avatars/
    ├── 1/
    │   └── avatar.jpg
    ├── 2/
    │   └── avatar.png
    └── 42/
        └── avatar.gif

Migration Safety:
- No changes to field definitions
- Only comments and documentation added
- All existing functionality preserved
- No database schema modifications required
"""
