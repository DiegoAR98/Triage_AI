"""Predefined anamnesis questions for the chat interface.

Supports multiple languages: English, Spanish, Portuguese (Brazil), Italian
"""

from dataclasses import dataclass, field


@dataclass
class AnamnesisQuestion:
    """Represents a single anamnesis question with translations."""

    number: int
    field_name: str
    description: str
    translations: dict[str, str] = field(default_factory=dict)

    def get_question(self, language: str = "en") -> str:
        """Get the question text in the specified language."""
        return self.translations.get(language, self.translations.get("en", ""))


# Language selection options
LANGUAGE_OPTIONS = {
    "en": "English",
    "es": "Español",
    "pt-BR": "Português (Brasil)",
    "it": "Italiano",
}

# Welcome messages by language
WELCOME_MESSAGES = {
    "en": "Welcome to Triage AI. I'll ask you a few questions to understand your symptoms and help direct you to the right care.",
    "es": "Bienvenido a Triage AI. Le haré algunas preguntas para entender sus síntomas y ayudarle a recibir la atención adecuada.",
    "pt-BR": "Bem-vindo ao Triage AI. Farei algumas perguntas para entender seus sintomas e ajudá-lo a receber o atendimento adequado.",
    "it": "Benvenuto a Triage AI. Le farò alcune domande per comprendere i suoi sintomi e aiutarla a ricevere le cure appropriate.",
}

# Language selection question
LANGUAGE_QUESTION = {
    "en": "Please select your preferred language:",
    "es": "Por favor seleccione su idioma preferido:",
    "pt-BR": "Por favor, selecione seu idioma preferido:",
    "it": "Per favore, selezioni la lingua preferita:",
}


# Predefined questions with translations
ANAMNESIS_QUESTIONS: list[AnamnesisQuestion] = [
    # Patient Demographics (Questions 1-5)
    AnamnesisQuestion(
        number=1,
        field_name="patient_name",
        description="Patient's full name",
        translations={
            "en": "What is your full name?",
            "es": "¿Cuál es su nombre completo?",
            "pt-BR": "Qual é o seu nome completo?",
            "it": "Qual è il suo nome completo?",
        }
    ),
    AnamnesisQuestion(
        number=2,
        field_name="date_of_birth",
        description="Patient's date of birth",
        translations={
            "en": "What is your date of birth?",
            "es": "¿Cuál es su fecha de nacimiento?",
            "pt-BR": "Qual é a sua data de nascimento?",
            "it": "Qual è la sua data di nascita?",
        }
    ),
    AnamnesisQuestion(
        number=3,
        field_name="phone_number",
        description="Contact phone number",
        translations={
            "en": "What is your phone number?",
            "es": "¿Cuál es su número de teléfono?",
            "pt-BR": "Qual é o seu número de telefone?",
            "it": "Qual è il suo numero di telefono?",
        }
    ),
    AnamnesisQuestion(
        number=4,
        field_name="emergency_contact_name",
        description="Emergency contact person",
        translations={
            "en": "Emergency contact name (who should we call in case of emergency)?",
            "es": "Nombre del contacto de emergencia (¿a quién debemos llamar en caso de emergencia)?",
            "pt-BR": "Nome do contato de emergência (quem devemos ligar em caso de emergência)?",
            "it": "Nome del contatto di emergenza (chi dobbiamo chiamare in caso di emergenza)?",
        }
    ),
    AnamnesisQuestion(
        number=5,
        field_name="emergency_contact_phone",
        description="Emergency contact phone",
        translations={
            "en": "Emergency contact phone number?",
            "es": "¿Número de teléfono del contacto de emergencia?",
            "pt-BR": "Número de telefone do contato de emergência?",
            "it": "Numero di telefono del contatto di emergenza?",
        }
    ),

    # Chief Complaint & Symptoms (Questions 6-14)
    AnamnesisQuestion(
        number=6,
        field_name="chief_complaint",
        description="Main reason for visit",
        translations={
            "en": "What brings you in today?",
            "es": "¿Qué le trae hoy?",
            "pt-BR": "O que o traz aqui hoje?",
            "it": "Cosa la porta qui oggi?",
        }
    ),
    AnamnesisQuestion(
        number=7,
        field_name="onset",
        description="When symptoms started",
        translations={
            "en": "When did this start?",
            "es": "¿Cuándo comenzó esto?",
            "pt-BR": "Quando isso começou?",
            "it": "Quando è iniziato?",
        }
    ),
    AnamnesisQuestion(
        number=8,
        field_name="pain_scale",
        description="Severity rating",
        translations={
            "en": "On a scale of 1-10, how severe is it?",
            "es": "En una escala del 1 al 10, ¿qué tan severo es?",
            "pt-BR": "Em uma escala de 1 a 10, qual a intensidade?",
            "it": "Su una scala da 1 a 10, quanto è grave?",
        }
    ),
    AnamnesisQuestion(
        number=9,
        field_name="location",
        description="Body location",
        translations={
            "en": "Where exactly is the problem located?",
            "es": "¿Dónde exactamente está ubicado el problema?",
            "pt-BR": "Onde exatamente está localizado o problema?",
            "it": "Dove si trova esattamente il problema?",
        }
    ),
    AnamnesisQuestion(
        number=10,
        field_name="radiation",
        description="Pain radiation",
        translations={
            "en": "Does the pain spread anywhere else?",
            "es": "¿El dolor se extiende a algún otro lugar?",
            "pt-BR": "A dor se espalha para algum outro lugar?",
            "it": "Il dolore si irradia altrove?",
        }
    ),
    AnamnesisQuestion(
        number=11,
        field_name="associated_symptoms",
        description="Associated symptoms",
        translations={
            "en": "Any other symptoms? (dizziness, nausea, fever, etc.)",
            "es": "¿Algún otro síntoma? (mareos, náuseas, fiebre, etc.)",
            "pt-BR": "Algum outro sintoma? (tontura, náusea, febre, etc.)",
            "it": "Altri sintomi? (vertigini, nausea, febbre, ecc.)",
        }
    ),
    AnamnesisQuestion(
        number=12,
        field_name="medical_history",
        description="Past medical history",
        translations={
            "en": "Do you have any medical conditions?",
            "es": "¿Tiene alguna condición médica?",
            "pt-BR": "Você tem alguma condição médica?",
            "it": "Ha qualche condizione medica?",
        }
    ),
    AnamnesisQuestion(
        number=13,
        field_name="current_medications",
        description="Current medications",
        translations={
            "en": "What medications are you currently taking?",
            "es": "¿Qué medicamentos está tomando actualmente?",
            "pt-BR": "Quais medicamentos você está tomando atualmente?",
            "it": "Quali farmaci sta assumendo attualmente?",
        }
    ),
    AnamnesisQuestion(
        number=14,
        field_name="allergies",
        description="Known allergies",
        translations={
            "en": "Do you have any allergies?",
            "es": "¿Tiene alguna alergia?",
            "pt-BR": "Você tem alguma alergia?",
            "it": "Ha qualche allergia?",
        }
    ),
]


def get_question(question_number: int, language: str = "en") -> AnamnesisQuestion | None:
    """Get a question by its number (1-indexed).

    Args:
        question_number: The question number (1-14)
        language: Language code (en, es, pt-BR)

    Returns:
        The AnamnesisQuestion or None if out of range
    """
    if 1 <= question_number <= len(ANAMNESIS_QUESTIONS):
        return ANAMNESIS_QUESTIONS[question_number - 1]
    return None


def get_question_text(question_number: int, language: str = "en") -> str | None:
    """Get the question text in the specified language.

    Args:
        question_number: The question number (1-14)
        language: Language code (en, es, pt-BR)

    Returns:
        The question text or None if out of range
    """
    question = get_question(question_number, language)
    if question:
        return question.get_question(language)
    return None


def get_total_questions() -> int:
    """Get the total number of anamnesis questions."""
    return len(ANAMNESIS_QUESTIONS)


def get_welcome_message(language: str = "en") -> str:
    """Get the welcome message in the specified language."""
    return WELCOME_MESSAGES.get(language, WELCOME_MESSAGES["en"])


def get_language_question(language: str = "en") -> str:
    """Get the language selection question text."""
    return LANGUAGE_QUESTION.get(language, LANGUAGE_QUESTION["en"])


def get_first_question(language: str = "en") -> str:
    """Get the first question to start the anamnesis."""
    return ANAMNESIS_QUESTIONS[0].get_question(language)
