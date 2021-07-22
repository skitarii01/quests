# quests
## Идея:
структуризация задач и мониторинг своей эффективности по системе https://time-blog.ru/metod-1-3-5/. В будущем возможны другие схемы составления задач на день(например стек задач на день без ограничений). Хранение данных происходит в таблицах Sqlite. Присутствует динамическое переопределение параметра сложности.

## Задачи, которые выполняет бот:
* составление дерева задач. То есть бот позволяет структуризировать поток задач/проектов в систему в виде дерева. У каждой задачи/квеста/проекта есть несколько параметров.
выбор задач на текущий день по системе 1-3-5. В (конце дня)/(по желанию пользователя) выборка обновляется, пользователь получает сводку о прошедшем дне и возможность составлять новую выборку
* предоставление статистики эффективности в определенный промежуток времени в виде графиков matplotlib

## 
## описание файлов
1. summaries - папка для хранения таблиц ключей пользователей вида (день, результат(процент выполненных заданий))
2. trees - папка для хранения данных деревьев квестов пользователей
3. Data.py - класс(и пара функций) для взаимодействия с таблицами sqlite
4. keyboards.py - файл с базовыми клавиатурами
5. loger.py - файл для изменения формата записываемых логов
6. main.py - код взаимодействия пользователя и бота
7. users_ids.db - база с id'шниками зарегистрированных пользователей

## изначальный макет проекта в виде файла pdf
В процессе разработки некоторые вещи пришлось убрать, так что макет не совсем актуален
[макет.pdf](https://github.com/skitarii01/quests/files/6862463/default.pdf)


## как осуществляется взаимодействие c интерфейсом
![image](https://user-images.githubusercontent.com/44062411/126644569-37eb15ec-3e79-4408-bf19-6d4cc6102471.png)
1. ... - перейти на уровень выше
2. главный - название родительского квеста на данном уровне, при нажатии в режиме "квесты" можно менять название, в режиме "текущие квесты" можно добавлять в пулл активных квестов
3. простой - вид сложности квеста(['простой', 'средний', 'сложный']), при нажатии можно менять
4. неважный - вид приоритета квеста(['неважный', 'не очень важный', 'важный']), при нажатии можно менять
5. описание - можно менять
6. добавить квест - добавляет пустой квест
7. удалить - удаление родительского квеста со всеми потомками
8. new_quest - квест-потомок на текущем уровне, при нажатии происходит переход на уровень ниже

