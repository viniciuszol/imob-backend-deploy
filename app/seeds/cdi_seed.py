from datetime import date
from app.database import SessionLocal
from app.models import CDI


# ==============================
# CONFIGURAÇÕES DO SEED
# ==============================
START_YEAR = 2010
END_YEAR = 2025

DEFAULT_PORCENTAGEM = 100.0
DEFAULT_CDI_AM = 0.0083
DEFAULT_CDI_PERCENTUAL_AM = 0.0083


def seed_cdi():
    db = SessionLocal()
    try:
        total_created = 0

        for year in range(START_YEAR, END_YEAR + 1):
            for month in range(1, 13):
                data = date(year, month, 1)

                exists = db.query(CDI).filter(CDI.data == data).first()
                if exists:
                    continue

                cdi = CDI(
                    data=data,
                    porcentagem=DEFAULT_PORCENTAGEM,
                    cdi_am=DEFAULT_CDI_AM,
                    cdi_percentual_am=DEFAULT_CDI_PERCENTUAL_AM
                )

                db.add(cdi)
                total_created += 1

        db.commit()
        print(f"✅ Seed CDI concluído. Registros criados: {total_created}")

    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao executar seed CDI: {e}")
        raise
    finally:
        db.close()


# Permite rodar direto via python
if __name__ == "__main__":
    seed_cdi()
