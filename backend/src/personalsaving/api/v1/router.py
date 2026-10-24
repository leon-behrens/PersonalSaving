from fastapi import APIRouter

# Aggregates every version 1 resource router. The application mounts this one
# router under /api/v1, so adding a resource is a single include_router call
# here rather than a change to the application factory.
router = APIRouter()

# Example, once the first resource exists:
#   from personalsaving.api.v1.accounts import router as accounts_router
#   router.include_router(accounts_router, prefix="/accounts", tags=["accounts"])
