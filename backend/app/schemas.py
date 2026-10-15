from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

LANGUAGES = {
    'en': ('English', 'eng_Latn'), 'hi': ('Hindi', 'hin_Deva'),
    'kn': ('Kannada', 'kan_Knda'), 'ta': ('Tamil', 'tam_Taml'),
    'te': ('Telugu', 'tel_Telu'), 'ml': ('Malayalam', 'mal_Mlym'),
    'mr': ('Marathi', 'mar_Deva'), 'bn': ('Bengali', 'ben_Beng'),
    'gu': ('Gujarati', 'guj_Gujr'), 'pa': ('Punjabi', 'pan_Guru'),
    'ur': ('Urdu', 'urd_Arab'), 'es': ('Spanish', 'spa_Latn'),
    'fr': ('French', 'fra_Latn'), 'de': ('German', 'deu_Latn'),
    'it': ('Italian', 'ita_Latn'), 'pt': ('Portuguese', 'por_Latn'),
    'ar': ('Arabic', 'arb_Arab'), 'ja': ('Japanese', 'jpn_Jpan'),
    'ko': ('Korean', 'kor_Hang'), 'zh-CN': ('Chinese', 'zho_Hans'),
    'ru': ('Russian', 'rus_Cyrl'), 'ne': ('Nepali', 'npi_Deva'),
}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class Credentials(BaseModel):
    model_config = ConfigDict(extra='forbid')
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    name: str = Field(default='Learner', min_length=1, max_length=80)


class TranslationRequest(StrictModel):
    text: str = Field(min_length=1, max_length=50000)
    src_lang: str = 'auto'
    target_lang: str = 'hi'
    tone: Literal['formal', 'casual', 'academic', 'professional', 'creative', 'conversational'] = 'professional'
    provider: Literal['auto', 'gemini', 'deep-translator', 'nllb'] = 'auto'
    allow_fallback: bool = True

    @field_validator('src_lang', 'target_lang')
    @classmethod
    def supported(cls, value, info):
        if value not in LANGUAGES and not (info.field_name == 'src_lang' and value == 'auto'):
            raise ValueError('Unsupported language')
        return value


class TranslationOutput(BaseModel):
    translated_text: str = Field(min_length=1, max_length=100000)
    detected_language: str = Field(min_length=2, max_length=30)


class TutorRequest(StrictModel):
    question: str = Field(min_length=1, max_length=2000)
    session_id: str = Field(pattern=r'^[a-zA-Z0-9-]{1,64}$')
    translation_id: str | None = None
    use_rag: bool = False


class TutorOutput(BaseModel):
    answer: str = Field(min_length=1, max_length=12000)
    alternatives: list[str] = Field(default_factory=list, max_length=5)
    exercises: list[str] = Field(default_factory=list, max_length=5)
    recommendations: list[str] = Field(default_factory=list, max_length=5)
    source_ids: list[str] = Field(default_factory=list, max_length=3)


class Vocabulary(StrictModel):
    word: str = Field(min_length=1, max_length=200)
    meaning: str = Field(min_length=1, max_length=1000)
    language: str = Field(min_length=2, max_length=20)


class Preferences(StrictModel):
    theme: Literal['light', 'dark'] = 'light'
    target_lang: str = 'hi'

    @field_validator('target_lang')
    @classmethod
    def language(cls, value):
        if value not in LANGUAGES:
            raise ValueError('Unsupported language')
        return value


class SpeechRequest(StrictModel):
    text: str = Field(min_length=1, max_length=5000)
    lang: str = 'en'

    @field_validator('lang')
    @classmethod
    def language(cls, value):
        if value not in LANGUAGES:
            raise ValueError('Unsupported language')
        return value
