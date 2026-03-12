import pytest
import os
from io import BytesIO
from app.models import db, User, UserRole, Ticket, TicketImage


UPLOAD_URL_TEMPLATE = "/api/tenant/tickets/{ticket_id}/images"


def _login(client, email, password="password123"):
    """Helper to get auth token."""
    resp = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    return resp.get_json()["access_token"]


# ===================================================
# FIXTURES
# ===================================================

@pytest.fixture()
def mgr(make_user):
    return make_user(name="Mgr", email="mgr@test.com", role=UserRole.MANAGER)


@pytest.fixture()
def managed_tenant(make_user, mgr):
    """Tenant assigned to a manager — can create tickets."""
    return make_user(
        name="Managed Tenant",
        email="mt@test.com",
        role=UserRole.TENANT,
        manager_id=mgr.id,
    )


@pytest.fixture()
def other_tenant(make_user):
    """Another tenant for permission testing."""
    return make_user(name="Other Tenant", email="ot@test.com", role=UserRole.TENANT)


@pytest.fixture()
def mt_token(client, managed_tenant):
    return _login(client, "mt@test.com")


@pytest.fixture()
def ot_token(client, other_tenant):
    return _login(client, "ot@test.com")


@pytest.fixture()
def sample_ticket(db, managed_tenant, mgr):
    """Pre-created ticket for testing."""
    t = Ticket(
        title="Broken door lock",
        description="Front door lock is stuck and won't open.",
        created_by=managed_tenant.id,
    )
    db.session.add(t)
    db.session.commit()
    return t


# ===================================================
# IMAGE UPLOAD TESTS
# ===================================================

class TestImageUpload:
    """Tests for POST /api/tenant/tickets/{ticket_id}/images"""

    def test_upload_valid_image(self, client, mt_token, sample_ticket):
        """Upload a valid PNG image."""
        file = BytesIO(b"fake image data")
        file.filename = "test.png"

        url = UPLOAD_URL_TEMPLATE.format(ticket_id=sample_ticket.id)
        resp = client.post(
            url,
            data={"image": (file, "test.png")},
            headers={"Authorization": f"Bearer {mt_token}"},
        )

        assert resp.status_code == 201
        body = resp.get_json()
        assert body["success"] is True
        assert body["image"]["ticket_id"] == sample_ticket.id
        assert "file_path" in body["image"]

        # Verify DB record created
        img = TicketImage.query.filter_by(ticket_id=sample_ticket.id).first()
        assert img is not None

    def test_upload_jpeg(self, client, mt_token, sample_ticket):
        """Verify JPEG files are accepted."""
        file = BytesIO(b"fake jpeg data")
        file.filename = "photo.jpg"

        url = UPLOAD_URL_TEMPLATE.format(ticket_id=sample_ticket.id)
        resp = client.post(
            url,
            data={"image": (file, "photo.jpg")},
            headers={"Authorization": f"Bearer {mt_token}"},
        )

        assert resp.status_code == 201
        assert resp.get_json()["success"] is True

    def test_upload_webp(self, client, mt_token, sample_ticket):
        """Verify WebP files are accepted."""
        file = BytesIO(b"fake webp data")
        file.filename = "image.webp"

        url = UPLOAD_URL_TEMPLATE.format(ticket_id=sample_ticket.id)
        resp = client.post(
            url,
            data={"image": (file, "image.webp")},
            headers={"Authorization": f"Bearer {mt_token}"},
        )

        assert resp.status_code == 201
        assert resp.get_json()["success"] is True

    def test_upload_no_file(self, client, mt_token, sample_ticket):
        """Request without image field should fail."""
        url = UPLOAD_URL_TEMPLATE.format(ticket_id=sample_ticket.id)
        resp = client.post(
            url,
            data={},
            headers={"Authorization": f"Bearer {mt_token}"},
        )

        assert resp.status_code == 400
        body = resp.get_json()
        assert body["success"] is False
        assert "No image provided" in body["message"]

    def test_upload_empty_filename(self, client, mt_token, sample_ticket):
        """File with empty filename should fail."""
        file = BytesIO(b"fake image")
        file.filename = ""

        url = UPLOAD_URL_TEMPLATE.format(ticket_id=sample_ticket.id)
        resp = client.post(
            url,
            data={"image": (file, "")},
            headers={"Authorization": f"Bearer {mt_token}"},
        )

        assert resp.status_code == 400
        body = resp.get_json()
        assert body["success"] is False
        assert "No image selected" in body["message"]

    def test_upload_invalid_extension(self, client, mt_token, sample_ticket):
        """File with unsupported extension should fail."""
        file = BytesIO(b"fake pdf content")
        file.filename = "document.pdf"

        url = UPLOAD_URL_TEMPLATE.format(ticket_id=sample_ticket.id)
        resp = client.post(
            url,
            data={"image": (file, "document.pdf")},
            headers={"Authorization": f"Bearer {mt_token}"},
        )

        assert resp.status_code == 400
        body = resp.get_json()
        assert body["success"] is False
        assert "not allowed" in body["message"].lower()

    def test_upload_nonexistent_ticket(self, client, mt_token):
        """Upload to non-existent ticket should fail."""
        file = BytesIO(b"fake image")
        file.filename = "test.png"

        url = UPLOAD_URL_TEMPLATE.format(ticket_id="nonexistent")
        resp = client.post(
            url,
            data={"image": (file, "test.png")},
            headers={"Authorization": f"Bearer {mt_token}"},
        )

        assert resp.status_code == 404
        body = resp.get_json()
        assert body["success"] is False
        assert "not found" in body["message"].lower()

    def test_upload_other_tenants_ticket(self, client, ot_token, sample_ticket):
        """Cannot upload to another tenant's ticket."""
        file = BytesIO(b"fake image")
        file.filename = "test.png"

        url = UPLOAD_URL_TEMPLATE.format(ticket_id=sample_ticket.id)
        resp = client.post(
            url,
            data={"image": (file, "test.png")},
            headers={"Authorization": f"Bearer {ot_token}"},
        )

        assert resp.status_code == 404
        body = resp.get_json()
        assert body["success"] is False

    def test_upload_requires_auth(self, client, sample_ticket):
        """Upload without auth token should fail."""
        file = BytesIO(b"fake image")
        file.filename = "test.png"

        url = UPLOAD_URL_TEMPLATE.format(ticket_id=sample_ticket.id)
        resp = client.post(
            url,
            data={"image": (file, "test.png")},
        )

        assert resp.status_code == 401

    def test_upload_requires_tenant_role(self, client, mgr, sample_ticket):
        """Manager should not be able to upload."""
        mgr_token = _login(client, "mgr@test.com")
        file = BytesIO(b"fake image")
        file.filename = "test.png"

        url = UPLOAD_URL_TEMPLATE.format(ticket_id=sample_ticket.id)
        resp = client.post(
            url,
            data={"image": (file, "test.png")},
            headers={"Authorization": f"Bearer {mgr_token}"},
        )

        assert resp.status_code == 403

    def test_upload_creates_activity_log(self, client, mt_token, sample_ticket, db):
        """Uploading an image should create an activity log."""
        from app.models import ActivityLog

        file = BytesIO(b"fake image")
        file.filename = "test.png"

        url = UPLOAD_URL_TEMPLATE.format(ticket_id=sample_ticket.id)
        resp = client.post(
            url,
            data={"image": (file, "test.png")},
            headers={"Authorization": f"Bearer {mt_token}"},
        )

        assert resp.status_code == 201

        # Check activity log created
        logs = ActivityLog.query.filter_by(ticket_id=sample_ticket.id).all()
        assert len(logs) > 0
        assert any("Uploaded image" in log.action for log in logs)

    def test_multiple_uploads_same_ticket(self, client, mt_token, sample_ticket):
        """Can upload multiple images to same ticket."""
        url = UPLOAD_URL_TEMPLATE.format(ticket_id=sample_ticket.id)

        # First upload
        file1 = BytesIO(b"image1 data")
        file1.filename = "pic1.png"
        resp1 = client.post(
            url,
            data={"image": (file1, "pic1.png")},
            headers={"Authorization": f"Bearer {mt_token}"},
        )
        assert resp1.status_code == 201

        # Second upload
        file2 = BytesIO(b"image2 data")
        file2.filename = "pic2.jpg"
        resp2 = client.post(
            url,
            data={"image": (file2, "pic2.jpg")},
            headers={"Authorization": f"Bearer {mt_token}"},
        )
        assert resp2.status_code == 201

        # Check both records exist
        imgs = TicketImage.query.filter_by(ticket_id=sample_ticket.id).all()
        assert len(imgs) == 2
