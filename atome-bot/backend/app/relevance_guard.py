import re


class DocumentRelevanceGuard:
    STRONG_KEYWORDS = {
        "atome",
        "atome card",
        "repayment",
        "statement",
        "billing",
        "refund",
        "transaction",
        "card",
        "otp",
        "cashback",
        "spending limit",
        "bill",
        "installment",
        "virtual card",
        "physical card",
        "merchant",
        "account details",
    }

    WEAK_KEYWORDS = {
        "payment",
        "due date",
        "pin",
        "qr ph",
        "credit",
        "support",
        "application",
        "declined",
        "failed",
        "bank",
        "e-wallet",
        "biller",
        "overdue",
        "refund details",
    }

    NEGATIVE_KEYWORDS = {
        "resume",
        "curriculum vitae",
        "work experience",
        "education",
        "project portfolio",
        "linkedin",
        "github profile",
        "salary",
        "job application",
        "interview",
    }

    MIN_SCORE = 0.22

    def evaluate(self, file_name: str, text: str) -> dict:
        normalized = self._normalize(text)
        if not normalized:
            return {
                "file_name": file_name,
                "score": 0.0,
                "decision": "rejected",
                "reason": "Document has no readable content.",
            }

        strong_hits = self._count_phrase_hits(normalized, self.STRONG_KEYWORDS)
        weak_hits = self._count_phrase_hits(normalized, self.WEAK_KEYWORDS)
        negative_hits = self._count_phrase_hits(normalized, self.NEGATIVE_KEYWORDS)
        token_count = max(1, len(normalized.split()))

        strong_component = min(0.65, strong_hits / 6)
        weak_component = min(0.25, weak_hits / 8)
        brand_component = 0.12 if "atome" in normalized else 0.0
        density_component = min(0.18, ((strong_hits + weak_hits) / token_count) * 25)
        penalty_component = min(0.6, negative_hits * 0.2)

        score = max(0.0, min(1.0, strong_component + weak_component + brand_component + density_component - penalty_component))
        decision = "accepted" if score >= self.MIN_SCORE else "rejected"

        if decision == "accepted":
            reason = f"Matched domain terms (strong={strong_hits}, weak={weak_hits})."
        else:
            reason = f"Low domain relevance (strong={strong_hits}, weak={weak_hits}, negative={negative_hits})."

        return {
            "file_name": file_name,
            "score": round(score, 4),
            "decision": decision,
            "reason": reason,
        }

    def _normalize(self, text: str) -> str:
        return re.sub(r"\s+", " ", text.lower()).strip()

    def _count_phrase_hits(self, text: str, phrases: set[str]) -> int:
        hits = 0
        for phrase in phrases:
            if phrase in text:
                hits += 1
        return hits
