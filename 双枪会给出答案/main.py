import sys
import time
import pygame
import settings

    
pygame.init()
pygame.display.set_caption("双枪会给出答案")

screen = pygame.display.set_mode(settings.screen_size)
screen_rect = screen.get_rect()


# 开始界面

screen.fill(settings.blue)
msg = pygame.font.SysFont("华文楷体", 96).render(f"双枪会给出答案", True, settings.red, settings.blue)
msg_rect = msg.get_rect()
screen.blit(msg, (250, 150))

msg = pygame.font.SysFont("华文楷体", 72).render(f"按空格键开始游戏", True, settings.white, settings.blue)
msg_rect = msg.get_rect()
screen.blit(msg, (300, 300))

mkblimage = pygame.transform.smoothscale(pygame.image.load(settings.mkbl_path), (400, 400))
screen.blit(mkblimage, (0, 400))

lbqhimage = pygame.transform.smoothscale(pygame.image.load(settings.lbqh_path), (400, 400))
screen.blit(lbqhimage, (800, 400))

pygame.display.flip()

Break = False
while not Break:
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                Break = True

pygame.time.set_timer(pygame.USEREVENT, 5000)

# 玩家创建
mkbl = settings.Player(settings.mkbl_path)
mkbl.rect.midleft = screen_rect.midleft
lbqh = settings.Player(settings.lbqh_path)
lbqh.rect.midright = screen_rect.midright


# 子弹
m_bullets = pygame.sprite.Group()
l_bullets = pygame.sprite.Group()


# 按键状态
keys = {
    pygame.K_LEFT: False,
    pygame.K_RIGHT: False,
    pygame.K_UP: False,
    pygame.K_DOWN: False,
    pygame.K_a: False,
    pygame.K_d: False,
    pygame.K_w: False,
    pygame.K_s: False
}

pygame.time.set_timer(pygame.USEREVENT, settings.cd * 1000)   # 定时

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        
        if event.type == pygame.USEREVENT:
            settings.spawn_health_pack()

        if event.type == pygame.KEYDOWN:
            if event.key in keys:
                keys[event.key] = True

            if event.key == pygame.K_SPACE:
                if len(m_bullets) < settings.AL:
                    m_bullet = settings.Bullet(mkbl.front[0], mkbl.front[1])
                    m_bullet.rect = pygame.Rect(settings.bullet_size)
                    m_bullet.rect.center = mkbl.rect.center
                    m_bullets.add(m_bullet)
            
            if event.key == pygame.K_RETURN:
                if len(l_bullets) < settings.AL:
                    l_bullet = settings.Bullet(lbqh.front[0], lbqh.front[1])
                    l_bullet.rect = pygame.Rect(settings.bullet_size)
                    l_bullet.rect.center = lbqh.rect.center
                    l_bullets.add(l_bullet)

        if event.type == pygame.KEYUP:
            if event.key in keys:
                keys[event.key] = False


    mkbl.face[0] = -1 if keys[pygame.K_a] else 1 if keys[pygame.K_d] else 0
    mkbl.face[1] = -1 if keys[pygame.K_w] else 1 if keys[pygame.K_s] else 0
    lbqh.face[0] = -1 if keys[pygame.K_LEFT] else 1 if keys[pygame.K_RIGHT] else 0
    lbqh.face[1] = -1 if keys[pygame.K_UP] else 1 if keys[pygame.K_DOWN] else 0

    if mkbl.face != [0, 0]:
        mkbl.front = mkbl.face[:]
    if lbqh.face != [0, 0]:
        lbqh.front = lbqh.face[:]
    

    mkbl.rect.x += mkbl.face[0] * settings.speed
    mkbl.rect.y += mkbl.face[1] * settings.speed
    lbqh.rect.x += lbqh.face[0] * settings.speed
    lbqh.rect.y += lbqh.face[1] * settings.speed

    if mkbl.rect.left < 0 or mkbl.rect.right > screen_rect.right:
        mkbl.rect.x -= mkbl.face[0] * settings.speed
    if mkbl.rect.top < 0 or mkbl.rect.bottom > screen_rect.bottom:
        mkbl.rect.y -= mkbl.face[1] * settings.speed
    if lbqh.rect.left < 0 or lbqh.rect.right > screen_rect.right:
        lbqh.rect.x -= lbqh.face[0] * settings.speed
    if lbqh.rect.top < 0 or lbqh.rect.bottom > screen_rect.bottom:
        lbqh.rect.y -= lbqh.face[1] * settings.speed

    txt_font = pygame.font.SysFont('华文楷体', 24)
    m_HP = txt_font.render(f"马可波罗 HP: {mkbl.HP}", True, settings.red, settings.blue)
    m_HP_rect = m_HP.get_rect()
    m_HP_rect = (10, 10)
    l_HP = txt_font.render(f"鲁班七号 HP: {lbqh.HP}", True, settings.red, settings.blue)
    l_HP_rect = l_HP.get_rect()
    l_HP_rect = (1000, 10)
    

    screen.fill(settings.blue)
    screen.blit(m_HP, m_HP_rect)
    screen.blit(l_HP, l_HP_rect)
    screen.blit(mkbl.image, mkbl.rect)
    screen.blit(lbqh.image, lbqh.rect)

    bullets = list(m_bullets) + list(l_bullets)

    for bullet in bullets:

        bullet.rect.x += bullet.face[0] * settings.bullet_speed
        bullet.rect.y += bullet.face[1] * settings.bullet_speed
        if bullet in m_bullets:
            if bullet.rect.bottom < 0 or bullet.rect.top > screen_rect.height or bullet.rect.right < 0 or bullet.rect.left > screen_rect.width:
                m_bullets.remove(bullet)
            else:
                pygame.draw.rect(screen, settings.yellow, bullet)
        else:
            if bullet.rect.bottom < 0 or bullet.rect.top > screen_rect.height or bullet.rect.right < 0 or bullet.rect.left > screen_rect.width:
                l_bullets.remove(bullet)
            else:
                pygame.draw.rect(screen, settings.white, bullet)


    if pygame.sprite.spritecollide(mkbl, l_bullets, True):
        mkbl.HP -= lbqh.AP
        settings.play_explosion(screen, mkbl.rect)
        if mkbl.HP <= 0:
            screen.fill(settings.blue)
            msg = pygame.font.SysFont("华文楷体", 96).render(f"鲁班七号胜利", True, settings.red, settings.blue)
            msg_rect = msg.get_rect()
            msg_rect.right = screen_rect.right
            screen.blit(msg, msg_rect)

            lbqh.image = pygame.transform.smoothscale(pygame.image.load(settings.lbqh_path), (500, 500))
            screen.blit(lbqh.image, (350, 200))

            pygame.display.flip()
            time.sleep(2)
            pygame.quit()
            sys.exit()

            
    if pygame.sprite.spritecollide(lbqh, m_bullets, True):
        lbqh.HP -= mkbl.AP
        settings.play_explosion(screen, lbqh.rect)
        if lbqh.HP <= 0:
            screen.fill(settings.blue)
            msg = pygame.font.SysFont("华文楷体", 96).render(f"马可波罗胜利", True, settings.red, settings.blue)
            msg_rect = msg.get_rect()
            msg_rect.right = screen_rect.right
            screen.blit(msg, msg_rect)

            mkbl.image = pygame.transform.smoothscale(pygame.image.load(settings.mkbl_path), (500, 500))
            screen.blit(mkbl.image, (350, 200))

            pygame.display.flip()
            time.sleep(2)
            pygame.quit()
            sys.exit()


    if pygame.sprite.spritecollide(mkbl, settings.health_packs, True):
        mkbl.HP += settings.get_health
        if mkbl.HP > 100:
            mkbl.HP = 100

    if pygame.sprite.spritecollide(lbqh, settings.health_packs, True):
        lbqh.HP += settings.get_health
        if lbqh.HP > 100:
            lbqh.HP = 100

    settings.health_packs.draw(screen)
    
    pygame.display.flip()

    time.sleep(0.0008)