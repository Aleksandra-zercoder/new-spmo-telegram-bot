from __future__ import annotations

from aiogram import Dispatcher

from handlers.admin import router as admin_router
from handlers.courses import router as courses_router
from handlers.forms import router as forms_router
from handlers.services import router as services_router
from handlers.start import router as start_router
from handlers.symptoms import router as symptoms_router
from handlers.admin_symptoms import router as admin_symptoms_router
from handlers.leads_admin import router as leads_admin_router


def register_all_handlers(dp: Dispatcher) -> None:
    # Order matters when you add more specific handlers later.
    dp.include_router(admin_router)
    dp.include_router(start_router)
    dp.include_router(symptoms_router)
    dp.include_router(services_router)
    dp.include_router(courses_router)
    dp.include_router(forms_router)
    dp.include_router(admin_symptoms_router)
    dp.include_router(leads_admin_router)

