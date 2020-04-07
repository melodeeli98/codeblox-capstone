# import pygame module in this program 
import pygame 
from tileops import tileToString


def draw(blocks, filename, isErr, errLoc):
    # activate the pygame library 
    # initiate pygame and give permission 
    # to use pygame's functionality. 
    pygame.init() 

    #blocks = [[14,26,1,10,22,5],[41,14,-1,-1,-1,-1]]
    rows = len(blocks)
    cols = len(blocks[0])
    
    # define the RGB value for white, 
    #  green, blue colour . 
    white = (255, 255, 255) 
    green = (0, 255, 0) 
    blue = (0, 0, 128)
    paleblue = (204, 255, 255)
    black = (0,0,0)
    red = (255,0,0)
    
    # assigning values to X and Y variable 
    X = 800
    Y = 800
    
    # create the display surface object 
    # of specific dimension..e(X, Y). 
    display_surface = pygame.display.set_mode((X, Y )) 
    
    # infinite loop 
    while True : 
    
        # completely fill the surface object 
        # with white color 
        display_surface.fill(white) 

        # create a font object. 
        # 1st parameter is the font file 
        # which is present in pygame. 
        # 2nd parameter is size of the font 
        font = pygame.font.Font('freesansbold.ttf', 20) 

        block_size = 100

        rect = pygame.Rect(0, 0, block_size, block_size)
        pygame.draw.rect(display_surface, black, rect, 1)
        text = font.render("master", True, red, white)
        textRect = text.get_rect()
        textRect.center = (block_size//2, block_size // 2)
        display_surface.blit(text, textRect)

        for y in range(rows):
            for x in range(cols):
                if blocks[y][x] != -1:
                    text = font.render(tileToString(blocks[y][x]), True, black, white)

                    rect = pygame.Rect(x*(block_size+1), (y+1)*(block_size+1), block_size, block_size)
                    pygame.draw.rect(display_surface, black, rect, 1)
                    textRect = text.get_rect()
                    textRect.center = (x*(block_size+1) + block_size//2, (y+1)*(block_size+1) + block_size // 2)
                    display_surface.blit(text, textRect)
    
        # iterate over the list of Event objects 
        # that was returned by pygame.event.get() method. 
        for event in pygame.event.get() : 
    
            # if event object type is QUIT 
            # then quitting the pygame 
            # and program both. 
            if event.type == pygame.QUIT : 
    
                # deactivates the pygame library 
                pygame.quit() 
    
                # quit the program. 
                quit() 
    
            # Draws the surface object to the screen.   
            pygame.display.update()  
