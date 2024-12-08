import sqlite3
from typing import Optional, List, Tuple

def logger(statement):
    print(f"""
--------------------------------------------------------
Executing:
{statement}
--------------------------------------------------------
""")

class DataBase:
    def __init__(self, path_to_db='admin/db.sqlite3'):
        self.path_to_db = path_to_db

    @property
    def connection(self):
        return sqlite3.connect(self.path_to_db)

    def execute(self, sql: str, parameters: tuple = None, fetchone=False, fetchall=False, commit=False):
        if not parameters:
            parameters = ()
        connection = self.connection
        connection.set_trace_callback(logger)
        cursor = connection.cursor()
        data = None
        cursor.execute(sql, parameters)

        if commit:
            connection.commit()
        if fetchall:
            data = cursor.fetchall()
        if fetchone:
            data = cursor.fetchone()
        connection.close()
        return data

    def add_user(self, fullname: str, user_id: int, username: str = None, referral_code: str = None):
        """Yangi foydalanuvchi qo'shish"""
        sql = """
        INSERT INTO konkurs_user (
            fullname, 
            telegram_id, 
            username, 
            score, 
            referral_code, 
            is_active,
            is_referral_counted,
            created_at
        ) 
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """
        parameters = (
            fullname,
            user_id,
            username,
            0,
            referral_code,
            True,
            False,
        )
        self.execute(sql, parameters=parameters, commit=True)

    def get_user_by_chat_id(self, telegram_id: int):
        """
        Telegram ID bo'yicha foydalanuvchini olish

        Args:
            telegram_id (int): Foydalanuvchi telegram ID si

        Returns:
            tuple: Foydalanuvchi ma'lumotlari
        """
        sql = "SELECT * FROM konkurs_user WHERE telegram_id = ?"
        return self.execute(sql, (telegram_id,), fetchone=True)

    def get_user_by_referral(self, referral_code: str):
        """Referal kod bo'yicha foydalanuvchini olish"""
        sql = "SELECT * FROM konkurs_user WHERE referral_code = ?"
        return self.execute(sql, (referral_code,), fetchone=True)

    def get_top_users_by_score(self, top_n=20):
        """Eng ko'p ball to'plagan foydalanuvchilarni olish"""
        sql = """
        SELECT fullname, score, telegram_id 
        FROM konkurs_user
        WHERE is_active = 1
        ORDER BY score DESC
        LIMIT ?
        """
        return self.execute(sql, (top_n,), fetchall=True)

    def get_score_by_id(self, telegram_id: int):
        """
        Foydalanuvchi ballini olish

        Args:
            telegram_id (int): Foydalanuvchi telegram ID si

        Returns:
            int: Foydalanuvchi bali
        """
        sql = "SELECT score FROM konkurs_user WHERE telegram_id = ?"
        result = self.execute(sql, (telegram_id,), fetchone=True)
        return result[0] if result else None

    def give_referral_bonus(self, referrer_id: int, referred_id: int) -> bool:
        """
        Referral bonus berish

        Args:
            referrer_id (int): Taklif qilgan foydalanuvchi ID si
            referred_id (int): Taklif qilingan foydalanuvchi ID si

        Returns:
            bool: Bonus berildi yoki yo'qligi
        """
        try:
            # Referral statusni tekshirish
            referred_user = self.get_user_by_chat_id(referred_id)
            if not referred_user:
                print(f"Referred user not found: {referred_id}")
                return False

            # is_referral_counted indeksi 6-o'rinda
            if referred_user[6]:  # Agar oldin hisoblangan bo'lsa
                print(f"Referral already counted for user {referred_id}")
                return False

            # Ball berish va status o'zgartirish
            connection = self.connection
            try:
                cursor = connection.cursor()

                # Ball qo'shish
                cursor.execute(
                    "UPDATE konkurs_user SET score = score + 10 WHERE telegram_id = ?",
                    (referrer_id,)
                )

                # Hisoblanganini belgilash
                cursor.execute(
                    "UPDATE konkurs_user SET is_referral_counted = 1 WHERE telegram_id = ?",
                    (referred_id,)
                )

                connection.commit()
                print(f"Referral bonus given: referrer={referrer_id}, referred={referred_id}")
                return True

            except Exception as e:
                print(f"Error in transaction: {e}")
                connection.rollback()
                return False
            finally:
                connection.close()

        except Exception as e:
            print(f"Error in give_referral_bonus: {e}")
            return False

    def check_and_create_referral(self, referrer_id: int, referred_id: int) -> bool:
        """
        Referral aloqani yaratish

        Args:
            referrer_id (int): Taklif qilgan foydalanuvchi ID si
            referred_id (int): Taklif qilingan foydalanuvchi ID si

        Returns:
            bool: Muvaffaqiyatli yaratilgan yoki yo'qligi
        """
        try:
            # Avval referrer mavjudligini tekshiramiz
            referrer = self.get_user_by_chat_id(referrer_id)
            if not referrer:
                print(f"Referrer not found: {referrer_id}")
                return False

            # O'ziga o'zi referral bo'lishni oldini olish
            if referrer_id == referred_id:
                print("Self referral attempted")
                return False

            # Referred foydalanuvchini yangilaymiz
            sql = """
            UPDATE konkurs_user 
            SET 
                referred_by_id = (SELECT id FROM konkurs_user WHERE telegram_id = ?),
                is_referral_counted = 0
            WHERE telegram_id = ?
            """
            self.execute(sql, (referrer_id, referred_id), commit=True)
            print(f"Referral created: {referrer_id} -> {referred_id}")
            return True

        except Exception as e:
            print(f"Error in check_and_create_referral: {e}")
            return False

    def update_user_score(self, telegram_id: int, points: int):
        """
        Foydalanuvchi ballini yangilash

        Args:
            telegram_id (int): Foydalanuvchi telegram ID si
            points (int): Qo'shiladigan ballar
        """
        try:
            current_score = self.get_score_by_id(telegram_id)
            if current_score is not None:
                new_score = current_score + points
                sql = "UPDATE konkurs_user SET score = ? WHERE telegram_id = ?"
                self.execute(sql, (new_score, telegram_id), commit=True)
                print(f"Score updated for {telegram_id}: {current_score} -> {new_score}")
            else:
                print(f"User not found: {telegram_id}")
        except Exception as e:
            print(f"Error in update_user_score: {e}")

    def mark_referral_counted(self, telegram_id: int):
        """
        Referral hisoblanganini belgilash

        Args:
            telegram_id (int): Foydalanuvchi telegram ID si
        """
        try:
            sql = "UPDATE konkurs_user SET is_referral_counted = 1 WHERE telegram_id = ?"
            self.execute(sql, (telegram_id,), commit=True)
            print(f"Marked referral as counted for user {telegram_id}")
        except Exception as e:
            print(f"Error in mark_referral_counted: {e}")

    def get_latest_award(self):
        """Eng so'nggi mukofotni olish"""
        sql = """
        SELECT title, description, image 
        FROM konkurs_award 
        WHERE is_active = 1 
        ORDER BY created_at DESC 
        LIMIT 1
        """
        return self.execute(sql, fetchone=True)

    def get_all_active_links(self):
        """Barcha faol kanallarni olish"""
        sql = """
        SELECT title, url 
        FROM konkurs_link 
        WHERE is_active = 1
        """
        return self.execute(sql, fetchall=True)

    def get_user_subscriptions(self, telegram_id: int) -> List[tuple]:
        """Foydalanuvchi obunalarini olish"""
        sql = """
        SELECT l.title, l.url, us.is_subscribed
        FROM konkurs_link l
        JOIN konkurs_usersubscription us ON l.id = us.channel_id
        JOIN konkurs_user u ON us.user_id = u.id
        WHERE u.telegram_id = ? AND l.is_active = 1
        """
        return self.execute(sql, (telegram_id,), fetchall=True)

    def update_subscription_status(self, telegram_id: int, channel_url: str, is_subscribed: bool):
        """Obuna statusini yangilash"""
        sql = """
        UPDATE konkurs_usersubscription
        SET is_subscribed = ?
        WHERE user_id = (SELECT id FROM konkurs_user WHERE telegram_id = ?)
        AND channel_id = (SELECT id FROM konkurs_link WHERE url = ?)
        """
        self.execute(sql, (is_subscribed, telegram_id, channel_url), commit=True)

    def update_statistics(self):
        """Kunlik statistikani yangilash"""
        # Avval bugungi statistika mavjudligini tekshirish
        check_sql = """
        SELECT id FROM konkurs_statistics 
        WHERE date = date('now')
        """
        existing_stats = self.execute(check_sql, fetchone=True)

        if existing_stats:
            # Mavjud statistikani yangilash
            sql = """
            UPDATE konkurs_statistics
            SET 
                total_users = (SELECT COUNT(*) FROM konkurs_user),
                active_users = (SELECT COUNT(*) FROM konkurs_user WHERE is_active = 1),
                total_subscriptions = (SELECT COUNT(*) FROM konkurs_usersubscription WHERE is_subscribed = 1),
                total_score = (SELECT COALESCE(SUM(score), 0) FROM konkurs_user),
                referral_counts = (SELECT COUNT(*) FROM konkurs_user WHERE is_referral_counted = 1)
            WHERE date = date('now')
            """
        else:
            # Yangi statistika yaratish
            sql = """
            INSERT INTO konkurs_statistics (
                date,
                total_users,
                active_users,
                total_subscriptions,
                total_score,
                referral_counts
            )
            SELECT
                date('now'),
                (SELECT COUNT(*) FROM konkurs_user),
                (SELECT COUNT(*) FROM konkurs_user WHERE is_active = 1),
                (SELECT COUNT(*) FROM konkurs_usersubscription WHERE is_subscribed = 1),
                (SELECT COALESCE(SUM(score), 0) FROM konkurs_user),
                (SELECT COUNT(*) FROM konkurs_user WHERE is_referral_counted = 1)
            """

        self.execute(sql, commit=True)

    def get_daily_statistics(self):
        """Kunlik statistikani olish"""
        sql = """
        SELECT 
            total_users, 
            active_users, 
            total_subscriptions, 
            total_score, 
            referral_counts
        FROM konkurs_statistics
        WHERE date = date('now')
        """
        return self.execute(sql, fetchone=True)