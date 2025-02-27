Xtreme Byte MAP Tool

Blender-аддон для импорта и экспорта файлов IPL и IDE из игры Grand Theft Auto: San Andreas. Поддерживает загрузку моделей в формате .dff, их размещение в сцене Blender, а также экспорт объектов обратно в форматы IPL и IDE с настройкой параметров (ID, LOD, TXD и т.д.).

Возможности
Импорт IPL: Загружает данные из .ipl файлов и создает объекты в сцене Blender на основе координат, поворотов и моделей .dff.
Экспорт IPL: Сохраняет объекты сцены в .ipl файл с поддержкой автоматического поиска LOD.
Экспорт IDE: Создает .ide файл с параметрами объектов (ID, TXD, дистанция отрисовки, флаги).
Настройка параметров: Установка ID, TXD, интерьеров, дистанции и LOD для выбранных объектов.
Проверка ошибок: Анализирует объекты на наличие проблем (например, длинные имена моделей или отсутствие LOD).

Установка:

1. Скачай последнюю версию аддона из релизов или клонируй репозиторий:
2. В Blender открой Edit > Preferences > Add-ons.
3. Нажми Install, выбери zip файл и активируй его, поставив галочку.

Инструкция по использованию аддона "Xtreme Byte" в Blender

  1. Открытие панели аддона
Убедись, что аддон установлен и зарегистрирован в Blender.

В области "View 3D" (3D-просмотр) в боковой панели (обычно справа, вкладка "N") найди раздел "Xtreme Tools". Если его нет, проверь, активирован ли аддон в настройках Blender (Edit > Preferences > Add-ons > Найди "Xtreme Byte").
Панель "Xtreme Byte" должна отобразиться с тремя основными разделами: "Настройка объектов", "Параметры моделей" и "Импорт и Экспорт".

  2. Настройка объектов
Этот раздел позволяет задать начальный ID для объектов.

В поле "Начальный ID" введи число, с которого начнётся нумерация ID для выделенных объектов (по умолчанию 0).
Нажми кнопку "Применить настройки", чтобы применить этот ID ко всем выделенным объектам. ID будут увеличиваться на 1 для каждого следующего объекта (например, 0, 1, 2 и т.д.).

  3. Параметры моделе
Здесь ты можешь настроить параметры для моделей, такие как текстуры, интерьеры, дистанции и флаги, а также параметры LOD.

Имя TXD: Введи имя текстурного архива (TXD), который будет использоваться для моделей.
Интерьер: Укажи номер интерьера (по умолчанию 0).
Дистанция: Задай значение дистанции видимости модели (по умолчанию 300.0).
Флаг: Введи числовое значение флага (по умолчанию 0).
Начало LOD: Укажи начальное значение для LOD-объектов (по умолчанию 0).
Выдели нужные объекты в сцене.
Нажми "Применить все", чтобы применить все указанные параметры ко всем выделенным объектам.
Если нужно сбросить или перезаписать настройки, нажми "Сбросить все", чтобы вернуть значения по умолчанию или применить текущие настройки заново.

  4. Импорт и Экспорт
Этот раздел позволяет импортировать данные из IPL-файлов и экспортировать объекты в форматы IPL и IDE.

 Импорт IPL

В поле "Путь к IPL" укажи путь к файлу IPL, который хочешь импортировать (нажми на кнопку с папкой, чтобы выбрать файл).
В поле "Папка DFF" укажи путь к папке, где находятся файлы DFF (модели), соответствующие объектам в IPL (нажми на кнопку с папкой, чтобы выбрать папку).
Нажми кнопку "Импортировать IPL", чтобы загрузить объекты из IPL-файла и связать их с моделями DFF. Убедись, что пути указаны правильно, иначе появится ошибка.

 Экспорт IPL

В поле "Экспорт IPL" укажи путь, куда хочешь сохранить файл IPL (нажми на кнопку с папкой, чтобы выбрать файл или папку).
Включи или выключи опцию "Автпоиск LOD", если хочешь автоматически находить LOD-объекты (по умолчанию выключено).
Выдели в сцене те объекты, которые хочешь экспортировать.
Нажми кнопку "Экспорт IPL", чтобы сохранить только выделенные объекты в файл IPL с указанными настройками.

 Экспорт IDE

В поле "Экспорт IDE" укажи путь, куда хочешь сохранить файл IDE (нажми на кнопку с папкой, чтобы выбрать файл или папку).
Выдели в сцене те объекты, которые хочешь экспортировать.
Нажми кнопку "Экспорт IDE", чтобы сохранить только выделенные объекты в файл IDE с указанными параметрами (TXD, дистанция, флаг и т.д.).

  5. Проверка ошибок

Нажми кнопку "Проверить ошибки", чтобы выявить возможные проблемы в выделенных объектах, такие как слишком длинные имена моделей, отсутствующие LOD или некорректные настройки.
Ошибки и предупреждения будут выведены в консоль Blender (окно "Console" или "System Console").

  Полезные советы:
  
Перед экспортом всегда выделяй только те объекты, которые нужно экспортировать — аддон будет работать только с выделенными объектами.
Убедись, что пути к файлам IPL, DFF и папкам указаны корректно, иначе импорт или экспорт не сработают.
Если настройки не применяются, проверь, выделены ли объекты, и повтори шаги из разделов "Настройка объектов" и "Параметры моделей".

XtremeByteGta — GitHub

Если у тебя есть вопросы или предложения, создавай issue!
