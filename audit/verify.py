import logging
from storage.database import Database
from config.settings import Settings
from audit.chain import AuditChain

logger = logging.getLogger(__name__)


class AuditVerifier:
    def __init__(self, db: Database):
        self.db = db

    def verify_chain(self) -> tuple[bool, str, int, int]:
        events = self.db.get_audit_events(limit=10000)

        if not events:
            return True, "No records to verify", 0, 0

        prev_hash = AuditChain.GENESIS

        for idx, event in enumerate(sorted(events, key=lambda x: x["timestamp"])):
            stored_prev_hash = event.get("prev_hash")

            if stored_prev_hash != prev_hash:
                return (
                    False,
                    f"Hash chain broken at record {event.get('id')} (event #{idx+1}): "
                    f"expected prev_hash={prev_hash}, got {stored_prev_hash}",
                    idx + 1,
                    len(events),
                )

            current_hash = event.get("record_hash")
            if not current_hash:
                return (
                    False,
                    f"Record {event.get('id')} missing record_hash",
                    idx + 1,
                    len(events),
                )

            prev_hash = current_hash

        return True, "AUDIT CHAIN: VALID", len(events), len(events)


def main():
    settings = Settings()
    db = Database(settings)
    verifier = AuditVerifier(db)

    is_valid, message, records_checked, total_records = verifier.verify_chain()

    if is_valid:
        print(f"✓ {message}")
        print(f"  records_checked: {records_checked}")
    else:
        print(f"✗ AUDIT CHAIN: BROKEN")
        print(f"  {message}")
        print(f"  first_invalid_record: {records_checked}")


if __name__ == "__main__":
    main()
