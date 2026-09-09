"""模型聚合导出。导入本包即注册全部表到 Base.metadata。"""
from .core import (
    Brand, BrandExpansion, Match, Project, ProjectLocation, User,
)
from .dictionary import BrandCategory, BrandTag, Dictionary, ProjectTag
from .people import BrandContact, BrandScore, ProjectContact, ProjectScore
from .pipeline import (
    CandidateList, CandidateListItem, CommunicationRecord, FollowupTask,
)
from .rbac import Permission, Role, RolePermission, UserRole
from .system import ApprovalRecord, AuditLog, ImportBatch
from .leasing import Lease, Merchant, ProjectCost, Receivable, Unit
from .assessment import MerchantAssessment, UnitBrandMatch
from .adjustment import UnitAdjustmentPlan

__all__ = [
    "User", "Brand", "BrandExpansion", "Project", "ProjectLocation", "Match",
    "Dictionary", "BrandCategory", "BrandTag", "ProjectTag",
    "BrandContact", "ProjectContact", "BrandScore", "ProjectScore",
    "CandidateList", "CandidateListItem", "CommunicationRecord", "FollowupTask",
    "ImportBatch", "ApprovalRecord", "AuditLog",
    "Role", "Permission", "UserRole", "RolePermission",
    # 出租经营域
    "Unit", "Merchant", "Lease", "Receivable", "ProjectCost",
    "UnitBrandMatch", "MerchantAssessment", "UnitAdjustmentPlan",
]
