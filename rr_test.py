# Testing class for rr.py
import unittest
import rr

class TestRRFunctions(unittest.TestCase):

    def test_get_longest_streak_bonus(self):
        # Test no streak before 3 consecutive runs
        self.assertEqual(rr.get_longest_streak_bonus(0), 0)
        self.assertEqual(rr.get_longest_streak_bonus(1), 0)
        self.assertEqual(rr.get_longest_streak_bonus(2), 0)

        # Test streak bonus starts at 3 consecutive runs 
        self.assertEqual(rr.get_longest_streak_bonus(3), 1)

        # Test various streak lengths and their bonuses for logarithmic growth
        self.assertEqual(rr.get_longest_streak_bonus(15), 2)
        self.assertEqual(rr.get_longest_streak_bonus(30), 3)

    def test_get_rank(self):
        # Test various RR values and positions
        self.assertEqual(rr.get_rank(0, 10), rr.Rank.BRONZE)
        self.assertEqual(rr.get_rank(100, 10), rr.Rank.SILVER)
        self.assertEqual(rr.get_rank(200, 10), rr.Rank.GOLD)
        self.assertEqual(rr.get_rank(300, 10), rr.Rank.PLATINUM)
        self.assertEqual(rr.get_rank(400, 10), rr.Rank.DIAMOND)
        self.assertEqual(rr.get_rank(500, 10), rr.Rank.MASTER)
        self.assertEqual(rr.get_rank(750, 10), rr.Rank.GRANDMASTER)
        self.assertEqual(rr.get_rank(750, 1), rr.Rank.USAIN_BOLT)
        self.assertEqual(rr.get_rank(750, 2), rr.Rank.GRANDMASTER)

    def test_get_rank_min_rr_for_usain_bolt(self):
        # Test that a user with less than 750 RR cannot be Usain Bolt
        self.assertEqual(rr.get_rank(0, 1), rr.Rank.BRONZE)
        self.assertEqual(rr.get_rank(100, 1), rr.Rank.SILVER)
        self.assertEqual(rr.get_rank(200, 1), rr.Rank.GOLD)
        self.assertEqual(rr.get_rank(300, 1), rr.Rank.PLATINUM)
        self.assertEqual(rr.get_rank(400, 1), rr.Rank.DIAMOND)
        self.assertEqual(rr.get_rank(500, 1), rr.Rank.MASTER)
        self.assertEqual(rr.get_rank(749, 1), rr.Rank.MASTER)

        # Test that a user with 750 or more RR can be Usain Bolt only if they are rank 1
        self.assertEqual(rr.get_rank(750, 1), rr.Rank.USAIN_BOLT)
        self.assertEqual(rr.get_rank(750, 2), rr.Rank.GRANDMASTER)
        self.assertEqual(rr.get_rank(750, 3), rr.Rank.GRANDMASTER)
        self.assertEqual(rr.get_rank(750, 4), rr.Rank.GRANDMASTER)
        self.assertEqual(rr.get_rank(750, 5), rr.Rank.GRANDMASTER)

    def test_get_distance_multiplier(self):
        # Test various distances and their multipliers
        # 0-1 mile: Linear from -1 to 0
        self.assertAlmostEqual(rr.get_distance_multiplier(0.0), -1.0)
        self.assertAlmostEqual(rr.get_distance_multiplier(0.5), -0.5)
        self.assertAlmostEqual(rr.get_distance_multiplier(0.99), -0.01)

        # < 1 mile: 1.0
        self.assertAlmostEqual(rr.get_distance_multiplier(1.0), 1.0)
        self.assertAlmostEqual(rr.get_distance_multiplier(1.5), 1.0)
        self.assertAlmostEqual(rr.get_distance_multiplier(2.0), 1.0)
        self.assertAlmostEqual(rr.get_distance_multiplier(3.0), 1.0)
        self.assertAlmostEqual(rr.get_distance_multiplier(5.0), 1.0)
        self.assertAlmostEqual(rr.get_distance_multiplier(10.0), 1.0)
    
    def test_get_distance_bonus(self):
        self.assertEqual(rr.get_distance_bonus(0.5), 0)
        self.assertEqual(rr.get_distance_bonus(1.0), 0)
        self.assertEqual(rr.get_distance_bonus(1.5), 1)
        self.assertEqual(rr.get_distance_bonus(2.0), 1)
        self.assertEqual(rr.get_distance_bonus(3.0), 2)
        self.assertEqual(rr.get_distance_bonus(5.0), 2)
        self.assertEqual(rr.get_distance_bonus(10.0), 3)
        

    def test_get_rank_name(self):
        self.assertEqual(rr.get_rank_name(rr.Rank.BRONZE), "Bronze")
        self.assertEqual(rr.get_rank_name(rr.Rank.SILVER), "Silver")
        self.assertEqual(rr.get_rank_name(rr.Rank.GOLD), "Gold")
        self.assertEqual(rr.get_rank_name(rr.Rank.PLATINUM), "Platinum")
        self.assertEqual(rr.get_rank_name(rr.Rank.DIAMOND), "Diamond")
        self.assertEqual(rr.get_rank_name(rr.Rank.MASTER), "Master")
        self.assertEqual(rr.get_rank_name(rr.Rank.GRANDMASTER), "Grandmaster")
        self.assertEqual(rr.get_rank_name(rr.Rank.USAIN_BOLT), "Usain Bolt")

    def test_get_rank_icon(self):
        self.assertEqual(rr.get_rank_icon(rr.Rank.BRONZE), "🥉")
        self.assertEqual(rr.get_rank_icon(rr.Rank.SILVER), "🥈")
        self.assertEqual(rr.get_rank_icon(rr.Rank.GOLD), "🥇")
        self.assertEqual(rr.get_rank_icon(rr.Rank.PLATINUM), "💿")
        self.assertEqual(rr.get_rank_icon(rr.Rank.DIAMOND), "💎")
        self.assertEqual(rr.get_rank_icon(rr.Rank.MASTER), "👑")
        self.assertEqual(rr.get_rank_icon(rr.Rank.GRANDMASTER), "🏆")
        self.assertEqual(rr.get_rank_icon(rr.Rank.USAIN_BOLT), "⚡")
        self.assertEqual(rr.get_rank_icon(None), "❓")
    
    def test_calculate_rr_logged(self):
        # Test RR calculation for various scenarios
        user = (None, None, None, 0, None, 0, 0, 0, 0)  # Starting user.
        self.assertEqual(rr.calculate_rr_logged(user, 0.5), 0)  # Distance < 1 mile, should lose nothing
        self.assertEqual(rr.calculate_rr_logged(user, 1.0), 25) # Base 25, no bonuses
        self.assertEqual(rr.calculate_rr_logged(user, 1.5), 26) # Base 25 + 1 distance bonus
        self.assertEqual(rr.calculate_rr_logged(user, 2.0), 26) # Base 25 + 1 distance bonus
        self.assertEqual(rr.calculate_rr_logged(user, 3.0), 27) # Base 25 + 2 distance bonus
        self.assertEqual(rr.calculate_rr_logged(user, 10.0), 28) # Base 25 + 3 distance bonus

if __name__ == '__main__':
    unittest.main()