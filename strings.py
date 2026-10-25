"""UI texts. Languages without a dict fall back to English."""

EN = dict(
    hint="Type a message...", send="Send", stop="Stop", settings="Settings", save="Save", cancel="Cancel",
    key="Anthropic API key", model="Model", nokey="Enter your API key in Settings first.",
    think="Thinking...", welcome="Hi! I'm BilimAi. Ask me anything - photos, files and voice work too.",
    search="Searching the web...", new="New", chats="Chats", rename="Rename", delete="Delete",
    copy="Copy", share="Share", listen="Listen", attach="File", voice="Voice", theme="Theme",
    dark="Dark", light="Light", size="Font size", small="Small", medium="Medium", large="Large",
    custom="Your own prompt (for the 'Custom' mode)", mode="Mode", web_on="Web: on", web_off="Web: off",
    copied="Copied", no_chats="No chats yet", untitled="New chat", err_attach="Could not add the file",
    err_voice="Voice input is not available", android_only="This feature works on Android only",
    photo="Photo", pdf="PDF", file="File", yes="Yes", no="No", confirm_del="Delete this chat?", error="Error",
    m_chat="Chat", m_tutor="Tutor", m_translator="Translator", m_coder="Coder", m_quiz="Quiz", m_custom="Custom",
)
RU = dict(
    hint="Напишите сообщение...", send="Отправить", stop="Стоп", settings="Настройки", save="Сохранить", cancel="Отмена",
    key="API-ключ Anthropic", model="Модель", nokey="Сначала введите API-ключ в настройках.",
    think="Думаю...", welcome="Привет! Я BilimAi. Спрашивайте что угодно — можно с фото, файлами и голосом.",
    search="Ищу в интернете...", new="Новый", chats="Чаты", rename="Переименовать", delete="Удалить",
    copy="Копировать", share="Поделиться", listen="Озвучить", attach="Файл", voice="Голос", theme="Тема",
    dark="Тёмная", light="Светлая", size="Размер шрифта", small="Мелкий", medium="Средний", large="Крупный",
    custom="Свой промпт (для режима «Свой»)", mode="Режим", web_on="Веб: вкл", web_off="Веб: выкл",
    copied="Скопировано", no_chats="Чатов пока нет", untitled="Новый чат", err_attach="Не удалось добавить файл",
    err_voice="Голосовой ввод недоступен", android_only="Эта функция работает только на Android",
    photo="Фото", pdf="PDF", file="Файл", yes="Да", no="Нет", confirm_del="Удалить чат?", error="Ошибка",
    m_chat="Беседа", m_tutor="Репетитор", m_translator="Переводчик", m_coder="Программист", m_quiz="Викторина", m_custom="Свой",
)
KK = dict(
    hint="Хабарлама жазыңыз...", send="Жіберу", stop="Тоқтату", settings="Баптау", save="Сақтау", cancel="Бас тарту",
    key="Anthropic API кілті", model="Модель", nokey="Алдымен баптаулардан API кілтін енгізіңіз.",
    think="Ойланып жатырмын...", welcome="Сәлем! Мен BilimAi. Кез келген сұрақ қойыңыз — фото, файл және дауыс та жұмыс істейді.",
    search="Интернеттен іздеп жатырмын...", new="Жаңа", chats="Чаттар", rename="Атын өзгерту", delete="Жою",
    copy="Көшіру", share="Бөлісу", listen="Тыңдау", attach="Файл", voice="Дауыс", theme="Тақырып",
    dark="Қараңғы", light="Жарық", size="Қаріп өлшемі", small="Кіші", medium="Орташа", large="Үлкен",
    custom="Өз нұсқаулығыңыз («Өзімдікі» режимі үшін)", mode="Режим", web_on="Веб: қосулы", web_off="Веб: өшірулі",
    copied="Көшірілді", no_chats="Чаттар жоқ", untitled="Жаңа чат", err_attach="Файлды қосу мүмкін болмады",
    err_voice="Дауыстық енгізу қолжетімсіз", android_only="Бұл функция тек Android-та жұмыс істейді",
    photo="Фото", pdf="PDF", file="Файл", yes="Иә", no="Жоқ", confirm_del="Чатты жою керек пе?", error="Қате",
    m_chat="Әңгіме", m_tutor="Репетитор", m_translator="Аудармашы", m_coder="Бағдарламашы", m_quiz="Викторина", m_custom="Өзімдікі",
)
TR = dict(
    hint="Mesaj yazın...", send="Gönder", stop="Durdur", settings="Ayarlar", save="Kaydet", cancel="İptal",
    key="Anthropic API anahtarı", model="Model", nokey="Önce ayarlardan API anahtarını girin.",
    think="Düşünüyorum...", welcome="Merhaba! Ben BilimAi. Her şeyi sorabilirsin — fotoğraf, dosya ve ses de çalışır.",
    search="İnternette arıyorum...", new="Yeni", chats="Sohbetler", rename="Yeniden adlandır", delete="Sil",
    copy="Kopyala", share="Paylaş", listen="Dinle", attach="Dosya", voice="Ses", theme="Tema",
    dark="Koyu", light="Açık", size="Yazı boyutu", small="Küçük", medium="Orta", large="Büyük",
    custom="Özel talimat ('Özel' modu için)", mode="Mod", web_on="Web: açık", web_off="Web: kapalı",
    copied="Kopyalandı", no_chats="Sohbet yok", untitled="Yeni sohbet", err_attach="Dosya eklenemedi",
    err_voice="Sesli giriş kullanılamıyor", android_only="Bu özellik yalnızca Android'de çalışır",
    photo="Fotoğraf", pdf="PDF", file="Dosya", yes="Evet", no="Hayır", confirm_del="Sohbet silinsin mi?", error="Hata",
    m_chat="Sohbet", m_tutor="Özel ders", m_translator="Çevirmen", m_coder="Yazılımcı", m_quiz="Bilgi yarışması", m_custom="Özel",
)

# name shown in spinner -> (language for the model, BCP-47 tag for voice/TTS)
LANGS = {
    "Русский": ("Russian", "ru-RU"), "Қазақша": ("Kazakh", "kk-KZ"), "English": ("English", "en-US"),
    "Türkçe": ("Turkish", "tr-TR"), "Українська": ("Ukrainian", "uk-UA"), "O'zbekcha": ("Uzbek", "uz-UZ"),
    "Deutsch": ("German", "de-DE"), "Français": ("French", "fr-FR"), "Español": ("Spanish", "es-ES"),
    "Chinese": ("Chinese", "zh-CN"), "Japanese": ("Japanese", "ja-JP"), "Korean": ("Korean", "ko-KR"),
}

MODES = ["chat", "tutor", "homework", "translator", "coder", "quiz", "custom"]
MODE_PROMPTS = {
    "chat": "You are BilimAi, a helpful, honest and knowledgeable AI assistant.",
    "tutor": ("You are BilimAi, a patient personal tutor. Explain step by step in simple words, give examples, "
              "and end with one short question that checks understanding. Guide the student toward the answer "
              "instead of only giving it, unless they just want the answer."),
    "translator": ("You are BilimAi, a professional translator. Translate the user's text into the reply language. "
                   "Output only the translation; add a short note only if something is ambiguous."),
    "homework": ("You are BilimAi, a homework helper. For a task (text or photo): restate it briefly, solve it step by step, "
                 "show the final answer clearly, then add a short check or tip. If the photo is unclear, say exactly what is unclear."),
    "coder": "You are BilimAi, an expert software engineer. Give correct, concise code in fenced code blocks and explain briefly.",
    "quiz": ("You are BilimAi, a quiz master. Ask one question at a time about the topic the user picks, wait for the "
             "answer, say whether it is correct and why, then continue with a slightly harder question."),
}


LEVEL_PROMPTS = {
    "school": "The user is a school student: use simple words and short steps.",
    "exam": "The user is preparing for university entrance exams (UNT/EGE/SAT style): focus on exam-relevant methods and typical mistakes.",
    "uni": "The user is a university student: be precise and use proper terminology.",
    "adult": "The user is an adult learner: be clear and practical.",
}
LEVELS = ["school", "exam", "uni", "adult"]

NEW_EN = dict(
    menu="Menu", study="Study cards", make_cards="Make cards", study_hint="Topic or text for flashcards (empty = use this chat)",
    stats="Progress", saved="Saved", star="Save", export="Export chat", level="Your level", l_school="School",
    l_exam="Exam prep", l_uni="University", l_adult="Adult", memory="About me (BilimAi remembers this)",
    pin="New PIN (4+ digits; empty = keep, 0 = remove)", server="Server URL (optional)", show_answer="Show answer",
    know="I know", again="Again", cards_done="Session complete", streak="Day streak", today="Today", total="Total",
    accuracy="Accuracy", decks="Your decks", loading="Working...", no_cards="Nothing to make cards from yet.",
    err_cards="Could not make cards", no_saved="Nothing saved yet", m_homework="Homework", app_lock="Enter PIN",
    wrong_pin="Wrong PIN", ok="OK", close="Close", key="Anthropic API key (or server token)", weak="Weak topics",
)
NEW_RU = dict(
    menu="Меню", study="Карточки", make_cards="Создать карточки", study_hint="Тема или текст для карточек (пусто = из этого чата)",
    stats="Прогресс", saved="Избранное", star="В избр.", export="Экспорт чата", level="Ваш уровень", l_school="Школа",
    l_exam="Подготовка к экзамену", l_uni="Университет", l_adult="Взрослый", memory="Обо мне (BilimAi это запомнит)",
    pin="Новый PIN (от 4 цифр; пусто = не менять, 0 = убрать)", server="Адрес сервера (необязательно)",
    show_answer="Показать ответ", know="Знаю", again="Ещё раз", cards_done="Сессия завершена", streak="Дней подряд",
    today="Сегодня", total="Всего", accuracy="Точность", decks="Ваши наборы", loading="Работаю...",
    no_cards="Не из чего делать карточки.", err_cards="Не удалось создать карточки", no_saved="Пока ничего не сохранено",
    m_homework="Домашка", app_lock="Введите PIN", wrong_pin="Неверный PIN", ok="ОК", close="Закрыть",
    key="API-ключ Anthropic (или токен сервера)", weak="Слабые темы",
)
NEW_KK = dict(
    menu="Мәзір", study="Карточкалар", make_cards="Карточка жасау", study_hint="Карточкаларға арналған тақырып немесе мәтін (бос = осы чаттан)",
    stats="Үлгерім", saved="Таңдаулы", star="Таңдаулыға", export="Чатты экспорттау", level="Деңгейіңіз", l_school="Мектеп",
    l_exam="Емтиханға дайындық", l_uni="Университет", l_adult="Ересек", memory="Мен туралы (BilimAi есте сақтайды)",
    pin="Жаңа PIN (4+ сан; бос = өзгертпеу, 0 = өшіру)", server="Сервер мекенжайы (міндетті емес)",
    show_answer="Жауапты көрсету", know="Білемін", again="Қайта", cards_done="Сессия аяқталды", streak="Қатарынан күн",
    today="Бүгін", total="Барлығы", accuracy="Дәлдік", decks="Жиынтықтарыңыз", loading="Жұмыс істеп жатыр...",
    no_cards="Карточка жасауға ештеңе жоқ.", err_cards="Карточкаларды жасау мүмкін болмады", no_saved="Әзірге ештеңе сақталмаған",
    m_homework="Үй тапсырмасы", app_lock="PIN енгізіңіз", wrong_pin="PIN қате", ok="ОК", close="Жабу",
    key="Anthropic API кілті (немесе сервер токені)", weak="Әлсіз тақырыптар",
)
NEW_TR = dict(
    menu="Menü", study="Kartlar", make_cards="Kart oluştur", study_hint="Kart yapılacak konu veya metin (boş = bu sohbet)",
    stats="İlerleme", saved="Kaydedilenler", star="Kaydet", export="Sohbeti dışa aktar", level="Seviyeniz", l_school="Okul",
    l_exam="Sınav hazırlığı", l_uni="Üniversite", l_adult="Yetişkin", memory="Hakkımda (BilimAi hatırlar)",
    pin="Yeni PIN (4+ hane; boş = değiştirme, 0 = kaldır)", server="Sunucu adresi (isteğe bağlı)",
    show_answer="Cevabı göster", know="Biliyorum", again="Tekrar", cards_done="Oturum tamamlandı", streak="Gün serisi",
    today="Bugün", total="Toplam", accuracy="Doğruluk", decks="Desteleriniz", loading="Çalışıyor...",
    no_cards="Kart yapacak bir şey yok.", err_cards="Kartlar oluşturulamadı", no_saved="Henüz kaydedilen yok",
    m_homework="Ödev", app_lock="PIN girin", wrong_pin="Yanlış PIN", ok="Tamam", close="Kapat",
    key="Anthropic API anahtarı (veya sunucu jetonu)", weak="Zayıf konular",
)
EN.update(NEW_EN); RU.update(NEW_RU); KK.update(NEW_KK); TR.update(NEW_TR)

# Extra interface languages: core texts translated, new feature texts fall back to English.
UK = dict(
    hint="Напишіть повідомлення...", send="Надіслати", stop="Стоп", settings="Налаштування", save="Зберегти", cancel="Скасувати",
    key="API-ключ Anthropic (або токен сервера)", model="Модель", nokey="Спочатку введіть API-ключ у налаштуваннях.",
    think="Думаю...", welcome="Привіт! Я BilimAi. Питайте будь-що — можна з фото, файлами та голосом.",
    search="Шукаю в інтернеті...", new="Новий", chats="Чати", rename="Перейменувати", delete="Видалити",
    copy="Копіювати", share="Поділитися", listen="Озвучити", attach="Файл", voice="Голос", theme="Тема",
    dark="Темна", light="Світла", size="Розмір шрифту", small="Дрібний", medium="Середній", large="Великий",
    custom="Свій промпт (для режиму «Свій»)", mode="Режим", web_on="Веб: увімк", web_off="Веб: вимк",
    copied="Скопійовано", no_chats="Чатів поки немає", untitled="Новий чат", err_attach="Не вдалося додати файл",
    err_voice="Голосовий ввід недоступний", android_only="Ця функція працює лише на Android",
    photo="Фото", file="Файл", yes="Так", no="Ні", confirm_del="Видалити чат?", error="Помилка",
    m_chat="Бесіда", m_tutor="Репетитор", m_translator="Перекладач", m_coder="Програміст", m_quiz="Вікторина", m_custom="Свій",
    menu="Меню", study="Картки", saved="Обране", export="Експорт чату", m_homework="Домашка", ok="ОК", close="Закрити",
)
UZ = dict(
    hint="Xabar yozing...", send="Yuborish", stop="To'xtatish", settings="Sozlamalar", save="Saqlash", cancel="Bekor qilish",
    key="Anthropic API kaliti (yoki server tokeni)", model="Model", nokey="Avval sozlamalarda API kalitini kiriting.",
    think="O'ylayapman...", welcome="Salom! Men BilimAi. Istalgan savolni bering — rasm, fayl va ovoz ham ishlaydi.",
    search="Internetdan qidiryapman...", new="Yangi", chats="Chatlar", rename="Nomini o'zgartirish", delete="O'chirish",
    copy="Nusxalash", share="Ulashish", listen="Tinglash", attach="Fayl", voice="Ovoz", theme="Mavzu",
    dark="Qorong'i", light="Yorug'", size="Shrift o'lchami", small="Kichik", medium="O'rta", large="Katta",
    custom="O'z ko'rsatmangiz («O'zimniki» rejimi uchun)", mode="Rejim", web_on="Veb: yoqilgan", web_off="Veb: o'chiq",
    copied="Nusxalandi", no_chats="Chatlar yo'q", untitled="Yangi chat", err_attach="Faylni qo'shib bo'lmadi",
    err_voice="Ovozli kiritish mavjud emas", android_only="Bu funksiya faqat Android'da ishlaydi",
    photo="Rasm", file="Fayl", yes="Ha", no="Yo'q", confirm_del="Chat o'chirilsinmi?", error="Xato",
    m_chat="Suhbat", m_tutor="Repetitor", m_translator="Tarjimon", m_coder="Dasturchi", m_quiz="Viktorina", m_custom="O'zimniki",
    menu="Menyu", study="Kartochkalar", saved="Saqlanganlar", export="Chatni eksport qilish", m_homework="Uy vazifasi", close="Yopish",
)
DE = dict(
    hint="Nachricht schreiben...", send="Senden", stop="Stopp", settings="Einstellungen", save="Speichern", cancel="Abbrechen",
    key="Anthropic-API-Schlüssel (oder Server-Token)", model="Modell", nokey="Gib zuerst den API-Schlüssel in den Einstellungen ein.",
    think="Ich denke nach...", welcome="Hallo! Ich bin BilimAi. Frag mich alles — Fotos, Dateien und Sprache gehen auch.",
    search="Suche im Web...", new="Neu", chats="Chats", rename="Umbenennen", delete="Löschen",
    copy="Kopieren", share="Teilen", listen="Vorlesen", attach="Datei", voice="Sprache", theme="Design",
    dark="Dunkel", light="Hell", size="Schriftgröße", small="Klein", medium="Mittel", large="Groß",
    custom="Eigener Prompt (für den Modus „Eigener“)", mode="Modus", web_on="Web: an", web_off="Web: aus",
    copied="Kopiert", no_chats="Noch keine Chats", untitled="Neuer Chat", err_attach="Datei konnte nicht hinzugefügt werden",
    err_voice="Spracheingabe nicht verfügbar", android_only="Diese Funktion gibt es nur auf Android",
    photo="Foto", file="Datei", yes="Ja", no="Nein", confirm_del="Chat löschen?", error="Fehler",
    m_chat="Chat", m_tutor="Nachhilfe", m_translator="Übersetzer", m_coder="Programmierer", m_quiz="Quiz", m_custom="Eigener",
    menu="Menü", study="Lernkarten", saved="Gespeichert", export="Chat exportieren", m_homework="Hausaufgaben", close="Schließen",
)
FR = dict(
    hint="Écrivez un message...", send="Envoyer", stop="Stop", settings="Réglages", save="Enregistrer", cancel="Annuler",
    key="Clé API Anthropic (ou jeton serveur)", model="Modèle", nokey="Saisissez d'abord la clé API dans les réglages.",
    think="Je réfléchis...", welcome="Bonjour ! Je suis BilimAi. Posez-moi n'importe quelle question — photos, fichiers et voix fonctionnent aussi.",
    search="Recherche sur le web...", new="Nouveau", chats="Discussions", rename="Renommer", delete="Supprimer",
    copy="Copier", share="Partager", listen="Écouter", attach="Fichier", voice="Voix", theme="Thème",
    dark="Sombre", light="Clair", size="Taille du texte", small="Petite", medium="Moyenne", large="Grande",
    custom="Votre propre prompt (mode « Perso »)", mode="Mode", web_on="Web : oui", web_off="Web : non",
    copied="Copié", no_chats="Aucune discussion", untitled="Nouvelle discussion", err_attach="Impossible d'ajouter le fichier",
    err_voice="Saisie vocale indisponible", android_only="Cette fonction n'existe que sur Android",
    photo="Photo", file="Fichier", yes="Oui", no="Non", confirm_del="Supprimer cette discussion ?", error="Erreur",
    m_chat="Discussion", m_tutor="Tuteur", m_translator="Traducteur", m_coder="Développeur", m_quiz="Quiz", m_custom="Perso",
    menu="Menu", study="Cartes", saved="Favoris", export="Exporter la discussion", m_homework="Devoirs", close="Fermer",
)
ES = dict(
    hint="Escribe un mensaje...", send="Enviar", stop="Parar", settings="Ajustes", save="Guardar", cancel="Cancelar",
    key="Clave API de Anthropic (o token del servidor)", model="Modelo", nokey="Primero introduce la clave API en Ajustes.",
    think="Pensando...", welcome="¡Hola! Soy BilimAi. Pregunta lo que quieras: también con fotos, archivos y voz.",
    search="Buscando en la web...", new="Nuevo", chats="Chats", rename="Renombrar", delete="Borrar",
    copy="Copiar", share="Compartir", listen="Escuchar", attach="Archivo", voice="Voz", theme="Tema",
    dark="Oscuro", light="Claro", size="Tamaño de letra", small="Pequeño", medium="Mediano", large="Grande",
    custom="Tu propio prompt (modo «Propio»)", mode="Modo", web_on="Web: sí", web_off="Web: no",
    copied="Copiado", no_chats="Aún no hay chats", untitled="Chat nuevo", err_attach="No se pudo añadir el archivo",
    err_voice="Entrada de voz no disponible", android_only="Esta función solo funciona en Android",
    photo="Foto", file="Archivo", yes="Sí", no="No", confirm_del="¿Borrar este chat?", error="Error",
    m_chat="Charla", m_tutor="Tutor", m_translator="Traductor", m_coder="Programador", m_quiz="Cuestionario", m_custom="Propio",
    menu="Menú", study="Tarjetas", saved="Guardados", export="Exportar chat", m_homework="Tareas", close="Cerrar",
)

NEW_EN3 = dict(account="Account", login="Log in", register="Sign up", logout="Log out", email="Email", password="Password",
    google="Continue with Google", plan="Plan", free="Free", pro="Pro", until="until", used="Requests today",
    upgrade="Upgrade to Pro", extend="Extend Pro", signed_in="Signed in:", limit_reached="Daily limit reached.",
    upgrade_q="Upgrade to Pro?", pay_unavailable="Payments are not set up yet.", network="No connection to the server")
NEW_RU3 = dict(account="Аккаунт", login="Войти", register="Регистрация", logout="Выйти", email="Email", password="Пароль",
    google="Войти через Google", plan="Тариф", free="Бесплатный", pro="Pro", until="до", used="Запросов сегодня",
    upgrade="Перейти на Pro", extend="Продлить Pro", signed_in="Вы вошли:", limit_reached="Дневной лимит исчерпан.",
    upgrade_q="Перейти на Pro?", pay_unavailable="Оплата пока не настроена.", network="Нет связи с сервером")
NEW_KK3 = dict(account="Аккаунт", login="Кіру", register="Тіркелу", logout="Шығу", email="Email", password="Құпия сөз",
    google="Google арқылы кіру", plan="Тариф", free="Тегін", pro="Pro", until="дейін", used="Бүгінгі сұраныстар",
    upgrade="Pro-ға өту", extend="Pro ұзарту", signed_in="Кірдіңіз:", limit_reached="Күнделікті лимит таусылды.",
    upgrade_q="Pro-ға өтесіз бе?", pay_unavailable="Төлем әлі бапталмаған.", network="Серверге қосылу жоқ")
NEW_TR3 = dict(account="Hesap", login="Giriş yap", register="Kayıt ol", logout="Çıkış yap", email="E-posta", password="Şifre",
    google="Google ile devam et", plan="Plan", free="Ücretsiz", pro="Pro", until="bitiş", used="Bugünkü istekler",
    upgrade="Pro'ya geç", extend="Pro'yu uzat", signed_in="Giriş yapıldı:", limit_reached="Günlük limit doldu.",
    upgrade_q="Pro'ya geçilsin mi?", pay_unavailable="Ödeme henüz ayarlanmadı.", network="Sunucuya bağlanılamadı")
EN.update(NEW_EN3); RU.update(NEW_RU3); KK.update(NEW_KK3); TR.update(NEW_TR3)

UI = {"English": EN, "Русский": RU, "Қазақша": KK, "Türkçe": TR, "Українська": UK,
      "O'zbekcha": UZ, "Deutsch": DE, "Français": FR, "Español": ES}
