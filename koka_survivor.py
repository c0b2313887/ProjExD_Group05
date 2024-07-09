import math
import os
import random
import sys
import time
import pygame as pg
import pygame


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：こうかとんSurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm


class Bird(pg.sprite.Sprite):
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }

    def __init__(self, num: int, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル
        """
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 1.0)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        self.imgs = {
            (+1, 0): img,  # 右
            (+1, -1): pg.transform.rotozoom(img, 45, 1.0),  # 右上
            (0, -1): pg.transform.rotozoom(img, 90, 1.0),  # 上
            (-1, -1): pg.transform.rotozoom(img0, -45, 1.0),  # 左上
            (-1, 0): img0,  # 左
            (-1, +1): pg.transform.rotozoom(img0, 45, 1.0),  # 左下
            (0, +1): pg.transform.rotozoom(img, -90, 1.0),  # 下
            (+1, +1): pg.transform.rotozoom(img, -45, 1.0),  # 右下
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10
        

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 1.0)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        current_speed = self.speed #current_speedにデフォルトのスピードを入れる
        if key_lst[pg.K_LSHIFT]: #シフト押したらスピード20にする
            current_speed = 20
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rect.move_ip(current_speed*sum_mv[0], current_speed*sum_mv[1])
        if check_bound(self.rect) != (True, True):
            self.rect.move_ip(-current_speed*sum_mv[0], -current_speed*sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]
        screen.blit(self.image, self.rect)


class Bomb(pg.sprite.Sprite):
    """
    爆弾に関するクラス
    """
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    def __init__(self, emy: "Enemy", bird: Bird):
        """
        爆弾円Surfaceを生成する
        引数1 emy：爆弾を投下する敵機
        引数2 bird：攻撃対象のこうかとん
        """
        super().__init__()
        rad = random.randint(10, 50)  # 爆弾円の半径：10以上50以下の乱数
        self.image = pg.Surface((2*rad, 2*rad))
        color = random.choice(__class__.colors)  # 爆弾円の色：クラス変数からランダム選択
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        # 爆弾を投下するemyから見た攻撃対象のbirdの方向を計算
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)  
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery+emy.rect.height//2
        self.speed = 6

    def update(self):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Beam(pg.sprite.Sprite):
    """
    ビームに関するクラス
    """
    def __init__(self, bird: Bird, angle0=0):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん
        """
        super().__init__()
        self.vx, self.vy = bird.dire
        angle = math.degrees(math.atan2(-self.vy, self.vx)) + angle0
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/beam.png"), angle, 2.0)
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery+bird.rect.height*self.vy
        self.rect.centerx = bird.rect.centerx+bird.rect.width*self.vx
        self.speed = 10    

    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()

class NeoBeam(pg.sprite.Sprite):
    """
    一度に複数方向へビームを発射するクラス
    """
    def __init__(self, bird: Bird, num: int):
        self.bird = bird
        self.num = num

    def gen_beams(self):
        """
        指定された数のビームを発射する
        """
        beams = []
        for angle in range(0, 360, int(360/self.num)):
            beams.append(Beam(self.bird, angle))
        return beams


class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """
    def __init__(self, obj: pg.sprite.Sprite, life: int):
        """
        爆発Surfaceを生成する
        引数1 obj：爆発する対象
        引数2 life：爆発の寿命
        """
        super().__init__()
        img = pg.image.load(f"fig/explosion.gif")
        self.image = pg.transform.rotozoom(img, 0, 2.0)
        self.rect = self.image.get_rect()
        self.rect.center = obj.rect.center
        self.life = life

    def update(self):
        """
        爆発の寿命を減じ，寿命が尽きたら爆発を消去する
        """
        self.life -= 1
        if self.life < 0:
            self.kill()


class Score:
    """
    スコアに関するクラス
    """
    def __init__(self):
        self.font = pg.font.Font(None, 60)
        self.value = 0

    def update(self, screen: pg.Surface):
        """
        スコアを更新する
        引数 screen：画面Surface
        """
        score_surf = self.font.render(f"Score: {self.value}", True, (0, 0, 0))
        screen.blit(score_surf, (10, 10))

class Gravity(pg.sprite.Sprite):
    """
    重力の影響を与える範囲を表現するクラス
    """
    def __init__(self, size):
        super().__init__()
        self.image = pg.Surface((2*size, 2*size), pg.SRCALPHA)
        pg.draw.circle(self.image, (0, 0, 0, 50), (size, size), size)
        self.rect = self.image.get_rect()
        self.rect.center = (WIDTH//2, HEIGHT//2)
        self.life = 500  # 存在するフレーム数

    def update(self):
        self.life -= 1
        if self.life < 0:
            self.kill()


class Enemy(pg.sprite.Sprite):
    """
    敵機に関するクラス
    """
    imgs = [pg.image.load(f"fig/alien{i}.png") for i in range(1, 4)]
    
    def __init__(self):
        super().__init__()
        self.image = random.choice(__class__.imgs)
        self.rect = self.image.get_rect()
        # 画面の外側のランダムな位置に初期化
        self.rect.center = random.choice([(random.randint(0, WIDTH), -50), 
                                          (random.randint(0, WIDTH), HEIGHT + 50), 
                                          (-50, random.randint(0, HEIGHT)), 
                                          (WIDTH + 50, random.randint(0, HEIGHT))])
        self.speed = 6  # 移動速度

    def update(self, target_pos):
        """
        敵機をマウスポインターに向かって移動させる
        引数 target_pos：マウスポインターの位置
        """
        direction = calc_orientation(self.rect, pg.Rect(target_pos, (1, 1)))
        self.rect.move_ip(self.speed * direction[0], self.speed * direction[1])


def main():
    pg.display.set_caption("真！こうかとん無双")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load(f"fig/aozora.jpg")
    scaled_bg_img = pygame.transform.scale(bg_img, (int(bg_img.get_width() * 0.7), int(bg_img.get_height() * 0.7)))
    score = Score()

    bird = Bird(3, (900, 400))
    bombs = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()
    gravities = pg.sprite.Group()

    tmr = 0
    clock = pg.time.Clock()
    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.add(Beam(bird))
            if event.type == pg.KEYDOWN and event.key == pg.K_RETURN:
                if score.value >= 200:
                    gravities.add(Gravity(400))
                    score.value -= 200
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE and key_lst[pg.K_LSHIFT]:  # シフト押下状態でスペースを押すと
                    neobeam = NeoBeam(bird, 5)  # ビームを複数発射
                    beams.add(neobeam.gen_beams())
                elif event.key == pg.K_SPACE:
                    beams.add(Beam(bird))

        screen.blit(scaled_bg_img, [0, 0])

        if tmr % 200 == 0:  # 200フレームに1回，敵機を出現させる
            emys.add(Enemy())

        mouse_pos = pg.mouse.get_pos()
        
        for emy in emys:
            if tmr % 100 == 0:  # 一定間隔で爆弾を投下
                bombs.add(Bomb(emy, bird))

        for emy in pg.sprite.groupcollide(emys, beams, True, True).keys():
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            score.value += 10  # 10点アップ
            bird.change_img(6, screen)  # こうかとん喜びエフェクト

        for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.value += 1  # 1点アップ

        if len(pg.sprite.spritecollide(bird, bombs, True)) != 0:
            bird.change_img(8, screen)  # こうかとん悲しみエフェクト
            score.update(screen)
            pg.display.update()
            time.sleep(2)
            return

        if len(pg.sprite.spritecollide(bird, emys, True)) != 0:
            bird.change_img(8, screen)  # こうかとん悲しみエフェクト
            score.update(screen)
            pg.display.update()
            time.sleep(2)
            return

        for gravity in gravities:
            for bomb in pg.sprite.spritecollide(gravity, bombs, True):
                exps.add(Explosion(bomb, 50))
                score.value += 1

            for bomb in pg.sprite.spritecollide(gravity, emys, True):
                exps.add(Explosion(bomb, 50))
                score.value += 10

        bird.update(key_lst, screen)
        beams.update()
        beams.draw(screen)
        emys.update(mouse_pos)  # 更新メソッドにマウスポインターの位置を渡す
        emys.draw(screen)
        bombs.update()
        bombs.draw(screen)
        exps.update()
        exps.draw(screen)
        gravities.update()
        gravities.draw(screen)
        score.update(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
