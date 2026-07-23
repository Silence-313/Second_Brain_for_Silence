"""Concept extractor — heuristic concept extraction from episode content. No LLM."""

import re
from collections import Counter

from agent.models.concepts import ExtractedConcept

_CJK_RE = re.compile(r"[一-鿿㐀-䶿]")
_HEADING_RE = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)
_ENGLISH_TERM_RE = re.compile(r"\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b|[a-z]+_[a-z]+|[a-z]+-[a-z]+")
_ENGLISH_PHRASE_RE = re.compile(r"\b[A-Za-z]{3,}\s+[A-Za-z]{3,}\b")

_NOISE_TRIGRAM = re.compile(
    r"(^[的是在了和就])|([的了着过]$)|(^[不太也没很都])|(^[这可那哪怎])"
)

_STRUCTURAL_LABELS = {
    "引言", "背景", "方法", "结果", "讨论", "结论", "总结", "摘要",
    "介绍", "概述", "分析", "建议", "附录", "参考文献", "致谢",
    "introduction", "background", "methods", "results", "discussion",
    "conclusion", "summary", "abstract", "appendix", "references",
}


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9一-鿿]+", "-", name.lower()).strip("-")


def _jaccard_words(a: str, b: str) -> float:
    set_a = set(a.lower().split())
    set_b = set(b.lower().split())
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


class ConceptExtractor:
    """Heuristic concept extraction. No LLM dependency."""

    def __init__(self, custom_stop_words: list[str] | None = None) -> None:
        self._stop_words: set[str] = set(custom_stop_words or [])
        self._stop_words |= {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "can", "shall",
            "to", "of", "in", "for", "on", "with", "at", "by", "from",
            "as", "into", "through", "during", "before", "after",
            "above", "below", "between", "under", "again", "further",
            "then", "once", "here", "there", "when", "where", "why",
            "how", "all", "both", "each", "few", "more", "most",
            "other", "some", "such", "no", "nor", "not", "only",
            "own", "same", "so", "than", "too", "very",
            "的", "了", "在", "是", "我", "有", "和", "就",
            "不", "人", "都", "一", "一个", "上", "也", "很",
            "到", "说", "要", "去", "你", "会", "着", "没有",
            "看", "好", "自己", "这", "他", "她", "它", "们",
            "那", "什么", "怎么", "哪", "为什么", "可以",
            "这个", "那个", "这些", "那些", "因为", "所以",
            "但是", "而且", "或者", "如果", "虽然", "然后",
        }

    def extract(
        self, content: str, existing_concepts: list[str] | None = None
    ) -> list[ExtractedConcept]:
        existing = set(existing_concepts or [])
        candidates: dict[str, ExtractedConcept] = {}

        self._extract_from_headings(content, candidates)
        self._extract_from_bigrams(content, candidates)
        self._extract_from_trigrams(content, candidates)
        self._extract_from_english_terms(content, candidates)

        self._match_existing(candidates, existing)
        results = self._rank_and_filter(candidates)
        results = self._deduplicate(results)
        return results[:6]

    def _extract_from_headings(
        self, content: str, candidates: dict[str, ExtractedConcept]
    ) -> None:
        for m in _HEADING_RE.finditer(content):
            text = m.group(2).strip()
            if not text or len(text) > 80:
                continue
            if text.lower() in _STRUCTURAL_LABELS:
                continue
            name = text.strip()
            slug = _slugify(name)
            existing = candidates.get(slug)
            if existing:
                self._upsert(candidates, slug, name, existing.confidence + 0.35, text)
            else:
                self._upsert(candidates, slug, name, 0.35, text)

    def _extract_from_bigrams(
        self, content: str, candidates: dict[str, ExtractedConcept]
    ) -> None:
        cjk_only = "".join(_CJK_RE.findall(content))
        if len(cjk_only) < 4:
            return

        freq: Counter[str] = Counter()
        for i in range(len(cjk_only) - 1):
            bg = cjk_only[i : i + 2]
            if bg not in self._stop_words:
                freq[bg] += 1

        if not freq:
            return

        max_freq = max(1, max(freq.values()))
        for bg, count in freq.items():
            if count < 2:
                continue
            score = (count / max_freq) * 0.3
            slug = _slugify(bg)
            self._upsert(candidates, slug, bg, score, bg)

    def _extract_from_trigrams(
        self, content: str, candidates: dict[str, ExtractedConcept]
    ) -> None:
        cjk_only = "".join(_CJK_RE.findall(content))
        if len(cjk_only) < 6:
            return

        freq: Counter[str] = Counter()
        for i in range(len(cjk_only) - 2):
            tg = cjk_only[i : i + 3]
            if not _NOISE_TRIGRAM.match(tg):
                freq[tg] += 1

        if not freq:
            return

        max_freq = max(1, max(freq.values()))
        for tg, count in freq.items():
            if count < 2:
                continue
            score = (count / max_freq) * 0.5
            slug = _slugify(tg)
            self._upsert(candidates, slug, tg, score, tg)

    def _extract_from_english_terms(
        self, content: str, candidates: dict[str, ExtractedConcept]
    ) -> None:
        for m in _ENGLISH_TERM_RE.finditer(content):
            term = m.group(0)
            if len(term) < 4 or term.lower() in self._stop_words:
                continue
            slug = _slugify(term)
            self._upsert(candidates, slug, term, 0.4, term)

        for m in _ENGLISH_PHRASE_RE.finditer(content):
            phrase = m.group(0)
            if len(phrase) < 6:
                continue
            slug = _slugify(phrase)
            self._upsert(candidates, slug, phrase, 0.4, phrase)

    def _match_existing(
        self,
        candidates: dict[str, ExtractedConcept],
        existing: set[str],
    ) -> None:
        for slug, concept in candidates.items():
            if slug in existing:
                candidates[slug] = ExtractedConcept(
                    name=concept.name,
                    slug=concept.slug,
                    confidence=min(1.0, concept.confidence + 0.2),
                    source_terms=concept.source_terms,
                )

    def _rank_and_filter(
        self, candidates: dict[str, ExtractedConcept]
    ) -> list[ExtractedConcept]:
        filtered = [c for c in candidates.values() if c.confidence >= 0.25]
        return sorted(filtered, key=lambda c: c.confidence, reverse=True)

    def _deduplicate(
        self, concepts: list[ExtractedConcept]
    ) -> list[ExtractedConcept]:
        result: list[ExtractedConcept] = []
        for c in concepts:
            is_dup = False
            for existing in result:
                if _jaccard_words(c.name, existing.name) >= 0.6:
                    is_dup = True
                    break
                if c.name in existing.name or existing.name in c.name:
                    is_dup = True
                    break
            if not is_dup:
                result.append(c)
        return result

    @staticmethod
    def _upsert(
        candidates: dict[str, ExtractedConcept],
        slug: str,
        name: str,
        score: float,
        source_term: str,
    ) -> None:
        existing = candidates.get(slug)
        if existing:
            confidence = max(existing.confidence, score)
            terms = list(set(existing.source_terms + [source_term]))
            candidates[slug] = ExtractedConcept(
                name=name, slug=slug, confidence=confidence, source_terms=terms
            )
        else:
            candidates[slug] = ExtractedConcept(
                name=name, slug=slug, confidence=score, source_terms=[source_term]
            )
