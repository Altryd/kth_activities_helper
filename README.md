### Внутри используется этот проект https://github.com/Altryd/osuParseMpLinks 
для его установки:
`pip install git+https://github.com/Altryd/osuParseMpLinks.git`

Основное, что нужно будет 100% перенести на Go:
- проект "https://github.com/Altryd/osuParseMpLinks" переписать на Go
- create_pairs() из api/matches.py
- parse_scrims_api() из api/matches.py
- Также в api/matches.py есть POST запрос на добавление и аппрув матча, его рано или поздно тоже надо будет переписать
- get_player() из api/player.py . Для этого понадобится сериализация Player и Matches в JSON как-то накумекать в Go
- show_matches() из routes/matches.py
- utility.py

elo_rating.py - дебаг элорейтинга, потом надо удалить, так как есть utility.py
app/models.py - описание БД на текущий момент
