import asyncio
import csv
import time

from config import settings, OSU_API_ASYNC
from osu_api.get_user import get_users, get_user
from csv import DictReader
from io import StringIO
from fastapi import HTTPException


async def main():
    with open("data_files/discord_members.csv", "rb") as fp:
        content = fp.read()
        content_str = content.decode('utf-8')
        csv_reader = DictReader(StringIO(content_str))

    not_found = []
    found = []
    for row in csv_reader:
        username = row['username'].strip()
        display_name = row['display_name']
        joined_at = row['joined_at']
        discord_id = row.get('discord_id', None)
        # print(username, display_name, joined_at, discord_id)
        osu_user = None
        try:
            # Теперь можно использовать await
            potential_osu_user = await get_user(username, OSU_API_ASYNC)
            if potential_osu_user.statistics.pp > 500:
                osu_user = potential_osu_user
        except HTTPException as ex:
            pass
        if not osu_user:
            time.sleep(1)
            try:
                # Теперь можно использовать await
                potential_osu_user = await get_user(display_name, OSU_API_ASYNC)
                if potential_osu_user.statistics.pp > 500:
                    osu_user = potential_osu_user
            except HTTPException as ex:
                pass
        if not osu_user:
            not_found.append({"username": username, "discord_id": discord_id, "osu_id": None, "pp": None,
                              "display_name": display_name})
        else:
            found.append({"username": osu_user.username, "discord_id": discord_id, "osu_id": osu_user.id,
                          "pp": osu_user.statistics.pp, "display_name": display_name})
            # found.append([username, display_name, discord_id, osu_user.id, osu_user.statistics.pp])
        time.sleep(3)
        # и далее всякие действия
    print(f"not found: {not_found}\n\n")
    print(f"found: {found}")
    headers = ["username", "discord_id", "osu_id", "pp", "display_name"]
    with open("data_files/result_2309.csv", "w", newline="", encoding='utf-8') as f:
        writer = csv.DictWriter(f, headers)
        writer.writeheader()
        writer.writerows(found)
        writer.writerows(not_found)


async def get_usernames():
    with open("data_files/players_to_add.csv", "rb") as fp:
        content = fp.read()
        content_str = content.decode('utf-8')
        csv_reader = DictReader(StringIO(content_str))
    usernames = []
    # not_found = []
    # found = []
    osu_ids = [row['osu_id'] for row in csv_reader]
    # osu_ids = [row['osu_id'] for row in csv_reader if len(row['osu_id']) > 0]
    osu_ids = [int(row) for row in osu_ids if len(row) > 0]
    batch_size = 40
    for i in range(0, len(osu_ids), batch_size):
        osu_ids_batch = osu_ids[i:i + batch_size]
        users = await get_users(osu_ids_batch, OSU_API_ASYNC)
        for osu_id in osu_ids_batch:
            if osu_id not in [user.id for user in users]:
                print(f"unluck: {osu_id}")
        for user in users:
            usernames.append(user.username)

    print(usernames)
    print(",".join(usernames))


class RatingNormalizer:
    def __init__(self, target_sr: float = 6.2, k: float = 2.0, rating_threshold: float = 5800.0,
                 max_rating_to_boost: float = 6700.0):
        self.target_sr = target_sr
        self.rating_threshold = rating_threshold
        self.max_rating_to_boost = max_rating_to_boost
        self.k = k

    def normalize(self, rating, star_rate):
        if star_rate <= self.target_sr:
            return rating * ((star_rate / self.target_sr) ** self.k)
        elif rating > self.max_rating_to_boost:
            return rating
        else:
            sr_excess = star_rate - self.target_sr
            # базовая прибавка за каждую "лишнюю" звезду
            base_boost = rating * 0.1 * sr_excess
            rating_deficit = max(0, self.rating_threshold - rating)
            deficit_boost = rating_deficit * \
                (star_rate / self.target_sr) ** self.k
            return rating + base_boost + deficit_boost
    """
    def normalize(self, rating, star_rate):
        if star_rate < self.target_sr:
            normalized_rating = rating * ((star_rate / self.target_sr) ** self.k)
        else:
            if rating < self.rating_threshold:
                normalized_rating = rating + (self.rating_threshold - rating) * (star_rate / self.target_sr) ** self.k
            else:
                normalized_rating = rating #  + 100 * (star_rate / self.target_sr) ** self.k
        return normalized_rating
    """


async def scan_ratings():
    with open("data_files/ratings.csv", "rb") as fp:
        content = fp.read()
        content_str = content.decode('utf-8')
        csv_reader = DictReader(StringIO(content_str))
    users = []
    rating_normalizer = RatingNormalizer()
    for row in csv_reader:
        rating, sr = int(row['rating']), float(row['sr'])
        normalized_rating = rating_normalizer.normalize(rating, sr)
        # users.append(row['username'], row['rating'], row['sr'], normalized_rating)
        users.append({"username": row['username'], "rating": row['rating'], "sr": row['sr'],
                      "normalized_rating": normalized_rating})
    headers = ["username", "rating", "sr", "normalized_rating"]
    with open("data_files/result_rating.csv", "w", newline="", encoding='utf-8') as f:
        writer = csv.DictWriter(f, headers)
        writer.writeheader()
        writer.writerows(users)


async def combine_files(ratings_file: str = "result_rating.csv", members_file: str = "result_2309.csv",
                        result_file: str = "result_combination.csv"):
    """
    Комбинирует файлы rating.csv (SIP) и информацию про пользователя (osu_id, discord_id, .. pp?)
    Returns:

    """
    with open(ratings_file, "rb") as fp:
        content = fp.read()
        content_str = content.decode('utf-8')
        csv_reader = DictReader(StringIO(content_str))
    users_ratings = {}
    users_with_rating = []
    for row in csv_reader:
        # rating, sr = int(row['rating']), float(row['sr'])
        # normalized_rating = rating_normalizer.normalize(rating, sr)
        # users.append(row['username'], row['rating'], row['sr'], normalized_rating)
        # users_ratings.append({"username": row['username'], "rating": row['rating'], "sr": row['sr'],
        #                      "normalized_rating": row['normalized_rating']})
        users_with_rating.append(row["username"])
        users_ratings[row["username"]] = {"rating": row['rating'], "sr": row['sr'],
                                          "normalized_rating": row['normalized_rating']}

    with open(members_file, "rb") as fp:
        content = fp.read()
        content_str = content.decode('utf-8')
        csv_reader = DictReader(StringIO(content_str))
    users_info = {}
    for row in csv_reader:
        users_info[row["username"]] = {"discord_id": row['discord_id'], "osu_id": row['osu_id'],
                                       "pp": row['pp'], "display_name": row['display_name']}
        # users_info.append({"username": row['username'], "discord_id": row['discord_id'], "osu_id": row['osu_id'],
        #                   "pp": row['pp'], "display_name": row['display_name']})
    result_list_with_info = []
    for username, user_info in users_info.items():
        if username in list(users_ratings.keys()):
            # user_info[username]["rating"] = users_ratings[username]["rating"]
            # user_info["sr"] = users_ratings[username]["sr"]
            # user_info["rating"] = users_ratings[username]["normalized_rating"]
            user_info.update({"username": username, "sr": users_ratings[username]["sr"],
                              "rating": users_ratings[username]["normalized_rating"]})
            result_list_with_info.append(user_info)
        else:
            user_info.update(
                {"username": username, "sr": None, "rating": None})
            result_list_with_info.append(user_info)
    headers = [
        "osu_id",
        "username",
        "pp",
        "rating",
        "sr",
        "discord_id",
        "display_name"]
    with open(result_file, "w", newline="", encoding='utf-8') as f:
        writer = csv.DictWriter(f, headers)
        writer.writeheader()
        writer.writerows(result_list_with_info)
    pass


if __name__ == "__main__":
    # usernames = ['SoundBoomer', 'Shimi', 'DaHuJka', 'fedotoff', 'Gtrr cat', 'Mentai', 'YungVenuz', 'Skrowell', 'hahahami', 'xunev', '_necroplasma', 'escace', 'tomoridesu-', 'Mori Calliope', 'DonnieGG', 'CpxG', 'DanFi', 'Uzer', 'Kirpich0', 'n0 head', 'MyAngelRasseru', 'KOTEL0K', 'doxxsan_', 'sareemaa', 'suntan', 'timmoltommol', 'vljoy209', 'Mariskiy Modnik', 'slimwish', 'Plurneet', 'Disha', 'Purpect', 'EPEMA', 'emo4kapro', 'ikigatsumaru', 'self[harm]ony', 'shevy1661', '3uma', '6mi6', 'xzeshnick', 'Akbo', 'kirndy', 'kiwoth', 'Fastik2006', 'Yatagarasu_GG', 'Alexveryanator', 'twotabby', 'hide', 'Bobyr', 'uhm', 'Plapa', 'kktova', 'player 228', 'Marfl', 'ded24lol', 'Yamezucu', 'VadimVAC', 'Kong', 'holub', 'Jabila', 'THE_LIPIK', 'Frindin', 'katalashka son', 'Aunn Komano', 'B4rISka', '10mi10', 'ItzZeroIce', 'silversnax', 'Stepa001', 'Twiner', 'ArlioN_-', 'ADMAX333', 'wriice', 'rxys', 'nucak', '- morgana -', 'swagych', 'baikalsk', '-Ansu-', 'xzeshnick', 'cfif [hjvjd', 'cryptile', 'lefrutit228', 'temka na', '_Demon1', 'N I K I T A', 'Wexxxxxy', 'Meowzarte', 'Welter', 'HosimachiSuisei', 'Whyolence', 'Inchainz', 'Hlebushek31', 'TOPXVLAD', 'Vivaru', 'Po1SoN3SS', 'frayzis', 'KpoJ1_MoHctp', 'Konetto', 'GET LOVED', 'Melifaro', 'steisha', 'RoVnDaskE', 'deGLe', 'Zoleks', 'sma11ow', 'silversnake', 'Auco', 'Kamensh1k', 'kanagava', 'Nennerce', '-4EPHbILLI-', 'Saruei', 'Salat1k009', 'VIPERSON', 'poltorawwwka', 'Maks0n4k', 'RagingDashie12', 'Mrkotikgg', 'ipad kid 2012', 'polyethylene', 'Kruzity', 'camaraderie', 'maxim', '-LS', 'Uruha Russia', 'LogiDASH', 'nikzz', 'Dester1337', 'John Doubletime', 'ZugamiRA', 'neimon', '_kurechi', 'MAKC0H', 'MicBoy5', 'zombirovannyj', 'akinami', '8mi8', 'Dealife', 'nuke employee', 'POMAH', 'Omores', '5mi5', 'slonikin211', 'RJbyM', 'K1rrubieL', 'LAZER DANYA 700', 'netraena', 'V A L E R A', 'AlSper05', 'Leary', 'ferzis', 'igrokpepe', '9mi9', 'apati', 'Wavewy', 'Timur0506', 'EternalDrain', 'dnomoreu', 'SilentSp', 'durashcka', '2003max', '-Ayame', 'Danc0', 'deviex', 'ReeStick', 'Prade', 'Zelretch', 'YungVenuz', 'user1337228', 'ffumiyomi', 'Gadfour', 'Ternafis', 'MIMOZA', 'Seall0w', 'whisper', 'metalvampir', 'paper clouds', 'timus123', 'Dakser', '-insomniac', 'frewayk', 'Amurskiu_Sanya', 'Decheg_777', 'HardLifeNH', 'ffroof', 'edikkiler212', 'Madaraha', 'ShuPLe', 'D4rgZ', 'VoiduNeedus', 'MotokEkb', 'VictorSkull', 'Alu', 'Vladislavich', 's4nrice', 'nxtgn', 'Vasteri', 'VANILLA KISSES', 'Tester', 'lokaoka', 'KOCT9H', 'NeODekVaT', 'CuDoPoBu4', 'PoMAH nuBoBAPoB', 'MAKCOH', 'Futhis', '-Ayano', 'SparrowRan', 'T-Light', 'DeSconTent', 'shadevr', 'NPG_Fenomen', 'Rick00j', 'Suzuha', 'Kolibri', 'Kuruminha', 'Kekich111', 'howtoplay', 'miageto', 'Loreal', 'Mostrax', 'desuqe', 'minefieldsurfer', 'DeadInside', '-HatsuneMiku', 'normanzerga', 'garab1k', 'Bullet', 'Ink', 'Tonusniy Nagib', 'Sandron', 'Theo', 'TrueDantist', 'shNzg0d', 'Lesocheck', 'twotabby', '-rixia-', '11iq pleer', 'Slotcore', 'Ququlu', '-Deity-', 'Vitya1437', 'ThankYou', 'Zavarka', 'RussianVaxei', 'Ontoryran', 'PLOV', 'KeRLi_', 'netnesanya', 'Snakeq', 'KortezR', 'Boriska', 'Tapok1322', 'Haroko', 'DK_', 'MyAngelMorph1ne', '11dvaN00lya', 'Lefy', 'JustRoxy', '1ce Shark', 'IxFire', 'Sheoss', 'Rushiki', 'Mohammad s', 'Rainbowtaves', 'SpidiMun', 'misha', 'n0 body', 'Stealer', 'squidstain', 'Markrum', 'Pezudos', 'Yuuka', '_kurayami', 'shax2', 'notsofast']
    # print(",".join(usernames))
    # asyncio.run(main())
    # asyncio.run(get_usernames())
    # asyncio.run(scan_ratings())
    asyncio.run(combine_files())
    """
    # Получаем osu_id по username через osu! API
    osu_user = await get_user(username, OSU_API_ASYNC)
    if not osu_user:
        raise HTTPException(status_code=404, detail=f"User {username} not found in osu! API")

    osu_id = osu_user.id

    # Проверяем наличие в БД
    db_user = await db.get(User, osu_id)
    if db_user:
        # Update: Показываем текущий и новый рейтинг
        preview.append(PreviewChange(
            action="update",
            username=username,
            osu_id=osu_id,
            new_elo_rating=rating,
            current_elo_rating=db_user.elo_rating,
            discord_id=discord_id if discord_id else db_user.discord_id
        ))
    else:
        # Add: Новый игрок
        preview.append(PreviewChange(
            action="add",
            username=username,
            osu_id=osu_id,
            new_elo_rating=rating,
            discord_id=discord_id
        ))
    """
