# -*- coding: utf-8 -*-
"""tests/test_cloud_sea.py - 云海预测系统自动化测试"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from analyzer import sunny_rating
from analyzer import _veto_clear_sky


class TestSunnyRatingV3:
    """日出评级 V3 测试 - LCL为主判据"""

    def test_perfect_shallow_fog(self):
        """浅雾(LCL<100) + 高RH + 好通透 + 高雾评分 -> 5星"""
        assert sunny_rating(cc=40, fog_score=80, above_positive=True,
                          rh=95, vis=25, score=70, lcl=50) == 5

    def test_good_shallow_fog(self):
        """浅雾 + RH>=85 + vis>=15 + fog_score>=45 -> 4星"""
        assert sunny_rating(cc=40, fog_score=60, above_positive=True,
                          rh=90, vis=18, score=65, lcl=80) == 4

    def test_ok_shallow_fog(self):
        """浅雾 + RH>=80 + vis>=10 -> 3星"""
        assert sunny_rating(cc=40, fog_score=30, above_positive=True,
                          rh=82, vis=12, score=50, lcl=90) == 3

    def test_medium_fog_high_score(self):
        """中层雾(100<LCL<300) + 高RH + 好通透 + fog>=60 -> 4星"""
        assert sunny_rating(cc=50, fog_score=60, above_positive=True,
                          rh=92, vis=20, score=60, lcl=200) == 4

    def test_medium_fog_normal(self):
        """中层雾 + 高RH + 好通透 + fog<60 -> 3星"""
        assert sunny_rating(cc=50, fog_score=40, above_positive=True,
                          rh=92, vis=18, score=55, lcl=200) == 3

    def test_thick_fog(self):
        """厚雾(300<LCL<500) + RH>=85 + fog>=30 -> 2星"""
        assert sunny_rating(cc=80, fog_score=40, above_positive=True,
                          rh=88, vis=5, score=50, lcl=450) == 2

    def test_very_thick_fog(self):
        """极厚雾(LCL>500) -> 最多2星"""
        assert sunny_rating(cc=100, fog_score=80, above_positive=True,
                          rh=98, vis=6, score=65, lcl=600) == 2

    def test_overcast_with_fog(self):
        """阴天+有雾(cc=100, LCL低) -> 2星(通透度瓶颈)"""
        assert sunny_rating(cc=100, fog_score=80, above_positive=True,
                          rh=98, vis=6.5, score=65, lcl=55) == 2

    def test_no_fog_below(self):
        """山顶在雾中(above_positive=False) -> 1星"""
        assert sunny_rating(cc=100, fog_score=0, above_positive=False,
                          rh=95, vis=5, score=5, lcl=100) == 1

    def test_dry_air_rejection_good_vis(self):
        """干燥气团(RH<65) + 高LCL>400 + 好通透 -> 2星(否决)"""
        assert sunny_rating(cc=15, fog_score=20, above_positive=True,
                          rh=50, vis=30, score=30, lcl=800) == 2

    def test_dry_air_rejection_poor_vis(self):
        """干燥气团 + 高LCL + 差通透 -> 1星"""
        assert sunny_rating(cc=15, fog_score=20, above_positive=True,
                          rh=50, vis=10, score=30, lcl=800) == 1

    def test_dry_air_loose(self):
        """RH<55 + LCL>200 -> 2星"""
        assert sunny_rating(cc=30, fog_score=40, above_positive=True,
                          rh=50, vis=20, score=40, lcl=300) == 2

    def test_lcl_parameter_affects_result(self):
        """验证lcl参数确实影响结果"""
        low_lcl = sunny_rating(cc=50, fog_score=60, above_positive=True,
                               rh=90, vis=20, score=60, lcl=80)
        high_lcl = sunny_rating(cc=50, fog_score=60, above_positive=True,
                                rh=90, vis=20, score=60, lcl=450)
        assert low_lcl > high_lcl, f"shallow({low_lcl}) should > thick({high_lcl})"

    def test_not_above_positive(self):
        """above_positive=False -> 1星"""
        assert sunny_rating(cc=10, fog_score=100, above_positive=False,
                          rh=100, vis=30, score=100, lcl=10) == 1

    def test_fog_score_boundary(self):
        """fog_score在45边界: 44->3星, 45->4星"""
        s44 = sunny_rating(cc=40, fog_score=44, above_positive=True,
                          rh=90, vis=18, score=60, lcl=80)
        s45 = sunny_rating(cc=40, fog_score=45, above_positive=True,
                          rh=90, vis=18, score=60, lcl=80)
        assert s44 == 3
        assert s45 == 4

    def test_medium_fog_boundary(self):
        """LCL在300m边界: 299->3+星, 301-><=2星"""
        s299 = sunny_rating(cc=50, fog_score=60, above_positive=True,
                           rh=92, vis=20, score=60, lcl=299)
        s301 = sunny_rating(cc=50, fog_score=60, above_positive=True,
                           rh=92, vis=20, score=60, lcl=301)
        assert s299 >= 3, f"LCL=299 should be >= 3 stars, got {s299}"
        assert s301 <= 2, f"LCL=301 should be <= 2 stars, got {s301}"


class TestVetoLogic:
    """否决逻辑测试"""

    def test_high_rh_exempts_clear_veto(self):
        """RH>=70%时晴空否决不生效"""
        result = _veto_clear_sky(wc_list=[0.1, 0.2], rh_list=[72, 75])
        assert len(result) == 3
        veto = result[0]
        assert veto is None, f"RH>=70% should exempt, got veto={veto}"

    def test_low_rh_clear_veto(self):
        """RH<70% + 晴空 -> 否决"""
        result = _veto_clear_sky(wc_list=[0.1, 0.2], rh_list=[55, 58])
        veto = result[0]
        assert veto is not None

    def test_cloudy_no_veto(self):
        """多云 -> 不否决"""
        result = _veto_clear_sky(wc_list=[3.0, 4.0], rh_list=[55, 58])
        veto = result[0]
        assert veto is None


class TestEndToEnd:
    """端到端测试: 验证真实数据可加载"""

    def test_load_weather_data(self):
        import json
        data_path = os.path.join(os.path.dirname(__file__), '..', 'data',
                                 'weather_data_2026-05-23.json')
        if not os.path.exists(data_path):
            return
        with open(data_path, encoding='utf-8') as f:
            data = json.load(f)
        assert 'peaks' in data
        assert len(data['peaks']) == 16

    def test_load_report_config(self):
        import json
        data_path = os.path.join(os.path.dirname(__file__), '..', 'data',
                                 'report_config_2026-05-23.json')
        if not os.path.exists(data_path):
            return
        with open(data_path, encoding='utf-8') as f:
            cfg = json.load(f)
        assert 'ranked' in cfg
        assert len(cfg['ranked']) == 16
        # diff<0 peaks should have score <= 10
        for r in cfg['ranked']:
            if r.get('diff', 0) < 0:
                assert r['score'] <= 10, f"{r['name']} diff<0 but score={r['score']}"
