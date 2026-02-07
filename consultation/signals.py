# from django.dispatch import Signal
#
# # Define signals
# consultation_paid = Signal()  # When consultation is paid
# consultation_accepted = Signal()  # When doctor accepts
# consultation_completed = Signal()  # When completed


from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from specialist.models import Doctor
from .models import DoctorAvailability, GlobalAvailabilityTemplate, ConsultationRequest
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Doctor)
def create_availability_for_new_doctor(sender, instance, created, **kwargs):
    """
    Yangi doctor yaratilganda yoki verify bo'lganda
    mavjud GlobalAvailabilityTemplate'lardan slotlar yaratish

    Trigger:
    - Doctor yangi yaratilganda (created=True)
    - Doctor verify bo'lganda (is_verified=True)
    - Doctor approve bo'lganda (user.is_approved=True)
    """

    # CRITICAL: Faqat role='doctor' bo'lgan userlar uchun
    if instance.user.role != 'doctor':
        logger.warning(
            f"Skipping slot creation for user {instance.user.id} - role is '{instance.user.role}', not 'doctor'")
        return

    # Faqat verified va approved doctorlar uchun
    if not instance.is_verified or not instance.user.is_approved:
        return

    # Agar allaqachon slotlari bo'lsa, skip qilish mumkin
    existing_slots = DoctorAvailability.objects.filter(doctor=instance.user).exists()
    if existing_slots and not created:
        return

    # Barcha active global template'larni olish
    templates = GlobalAvailabilityTemplate.objects.filter(is_active=True)

    if not templates.exists():
        logger.warning(f"No active GlobalAvailabilityTemplate found for doctor {instance.user.id}")
        return

    # Har bir template uchun slot yaratish
    created_count = 0
    for template in templates:
        # Agar bu sana va vaqt uchun allaqachon slot bo'lsa, skip
        exists = DoctorAvailability.objects.filter(
            doctor=instance.user,
            date=template.date,
            start_time=template.start_time,
            end_time=template.end_time
        ).exists()

        if not exists:
            DoctorAvailability.objects.create(
                doctor=instance.user,
                template=template,
                date=template.date,
                start_time=template.start_time,
                end_time=template.end_time,
                is_available=True
            )
            created_count += 1

    logger.info(
        f"✅ Created {created_count} availability slots for doctor {instance.user.first_name} (ID: {instance.user.id})")


@receiver(post_save, sender=GlobalAvailabilityTemplate)
def create_slots_for_all_doctors(sender, instance, created, **kwargs):
    """
    Yangi GlobalAvailabilityTemplate yaratilganda
    barcha verified doctorlar uchun slot yaratish

    Trigger:
    - Yangi template yaratilganda
    """

    if not created or not instance.is_active:
        return

    # Barcha verified va approved doctorlarni olish
    # CRITICAL: Faqat role='doctor' bo'lgan userlar
    doctors = Doctor.objects.filter(
        is_verified=True,
        user__is_approved=True,
        user__role='doctor'  # ← MUHIM: Faqat doctor role
    ).select_related('user')

    if not doctors.exists():
        logger.warning("No verified doctors found to create slots")
        return

    # Har bir doctor uchun slot yaratish
    created_count = 0
    for doctor in doctors:
        # Agar bu sana va vaqt uchun allaqachon slot bo'lsa, skip
        exists = DoctorAvailability.objects.filter(
            doctor=doctor.user,
            date=instance.date,
            start_time=instance.start_time,
            end_time=instance.end_time
        ).exists()

        if not exists:
            DoctorAvailability.objects.create(
                doctor=doctor.user,
                template=instance,
                date=instance.date,
                start_time=instance.start_time,
                end_time=instance.end_time,
                is_available=True
            )
            created_count += 1

    logger.info(f"✅ Created {created_count} slots for {doctors.count()} doctors from template {instance.id}")


# BONUS: UserModel approve bo'lganda ham tekshirish
try:
    from account.models import UserModel


    @receiver(post_save, sender=UserModel)
    def sync_doctor_availability_on_approval(sender, instance, created, **kwargs):
        """
        User approve bo'lganda doctor availability'ni yaratish

        CRITICAL: Faqat role='doctor' bo'lgan userlar uchun
        """
        # Faqat doctor role'ga ega userlar uchun
        if instance.role != 'doctor' or not instance.is_approved:
            return

        # Doctor modelini tekshirish
        try:
            doctor = Doctor.objects.get(user=instance)

            # Agar doctor verify va user approve bo'lsa, slotlar yaratish
            if doctor.is_verified:
                create_availability_for_new_doctor(
                    sender=Doctor,
                    instance=doctor,
                    created=False
                )
        except Doctor.DoesNotExist:
            pass

except ImportError:
    logger.warning("Could not import UserModel for signals")


@receiver(pre_delete, sender=ConsultationRequest)
def free_slot_on_consultation_delete(sender, instance, **kwargs):
    """
    ConsultationRequest o'chirilganda slotni avtomatik bo'shatish
    """
    if instance.availability_slot:
        slot = instance.availability_slot
        slot.is_available = True
        slot.consultation = None
        slot.save()
