from __future__ import annotations
import random
import sys
import time
from enum import Enum
from dataclasses import dataclass
from itertools import chain

SkillTuple = tuple["Skill", "Skill", "Skill"]

class SkillType(Enum):
    SLASH = 1
    PIERCE = 2
    BASH = 3
    @staticmethod
    def from_str(typetext: str):
        typetext = typetext.upper()
        if typetext == "SLASH":
            return SkillType.SLASH
        if typetext == "PIERCE":
            return SkillType.PIERCE
        if typetext == "BASH":
            return SkillType.BASH
        raise NameError

class ActionType(Enum):
    ONESIDE = 1
    CLASH = 2   


@dataclass(unsafe_hash=True)
class Resistance:
    slash: float
    pierce: float
    bash: float
    def from_type(self, skill_type: SkillType) -> float:
        if skill_type == SkillType.SLASH:
            return self.slash
        if skill_type == SkillType.PIERCE:
            return self.pierce
        return self.bash


#Class with all informations of ID
class Character:
    def __init__(
            self,
            name:str,
            maxhp:int,
            maxstag:int,
            sanity: int,
            skillcycle: list[int],
            spmin: int,
            spmax: int,
            resistance: Resistance,
            skills: SkillTuple
        ):
        self.name = name
        self.maxhp = maxhp
        self.curhp = maxhp
        self.maxstag = maxstag
        self.curstag = maxstag
        self.sanity = sanity
        self.skillcycle = skillcycle
        self.spmin = spmin
        self.spmax = spmax
        self.speed: int = 0
        self.resistance = resistance
        self.skills = skills
        self.deathtimer: int = 0
        self.staggertimer: int = 0

    def stagger(self):
        print(f"{self.name} is staggered!")
        self.staggertimer = 2

    def die(self):
        print(f"{self.name} is dead!")
        self.deathtimer = 3

    def set_speed(self):
        self.speed = random.randint(self.spmin, self.spmax)

    def is_alive(self):
        return self.curhp > 0
    
    def is_stagger(self):
        return self.curstag < 1

    def next_turn(self):
        self.set_speed()
        if self.deathtimer > 0:
            self.deathtimer -= 1
        if self.deathtimer == 0:
            self.curhp = self.maxhp
        if self.staggertimer > 0:
            self.staggertimer -= 1
        if self.staggertimer == 0:
            self.curstag = self.maxstag
    
    #Damage multiplier
    def find_mult(self, skill_type:SkillType) -> float:
        if self.is_stagger():
            return 2
        return self.resistance.from_type(skill_type)
    
    #Taking one direction damage
    def take_damage(self, damage: int):
        self.curhp -= damage
        if self.curstag != 0:
            self.curstag -= damage
        if self.curstag <= 0:
            self.curstag = 0
            self.stagger()
        if self.curhp <= 0:
            self.curhp = 0
            self.die()

    #Aim target of the action for the turn
    def target(self, targ: Character, skill_choice: int) -> ActionType:
        print(f"{self.name} targets {targ.name} with skill S{skill_choice} by speed of {self.speed}.")
        if isinstance(targ, BusCharacter):
            return ActionType.ONESIDE
        if self.speed > targ.speed:
            if targ.is_stagger():
                return ActionType.ONESIDE
            print(f"{self.name} is faster than {targ.name}, you can choose to perform one-side attack or clash")
            choice = 0
            while True:
                try:
                    choice = int(input("Enter 1 to perform one-side attack, 2 to match clash: "))
                    if choice < 1 or choice > 2:
                        print("Wrong input. Try again")
                    else:
                        break
                except ValueError:
                    print("Invalid input. Please enter a valid integer.")
            if choice == 1:
                return ActionType.ONESIDE
            return ActionType.CLASH
        return ActionType.ONESIDE
    
class BusCharacter(Character):
    def __init__(self):
        super().__init__("Mephistopheles", 50, 100, 0, assign_skillcycle(), 0, 0, Resistance(1, 1, 1), (Skill(0,0,0,"slash"), Skill(0,0,0,"slash"), Skill(0,0,0,"slash")))

    def next_turn(self):
        pass
    
class Team:
    def __init__(self, name: str, characters: list[Character]):
        self.name = name
        self.characters = characters

    def __repr__(self) -> str:
        ret_str = f"{self.name}'s Team"
        for char in self.characters:
            if isinstance(char, BusCharacter):
                ret_str += f"\n{self.name}'s {char.name} (Health: {char.curhp}/{char.maxhp})"
            elif char.is_alive():
                if char.is_stagger():
                    ret_str += f"\n{char.name} is staggered \n (Speed: 0, Sanity: {char.sanity}, Stagger: {char.curstag}/{char.maxstag}, Health: {char.curhp}/{char.maxhp})"
                else:
                    ret_str += f"\n{char.name} \n (Speed: {char.speed}, Sanity: {char.sanity}, Skill: (S{char.skillcycle[0]}/S{char.skillcycle[1]}), Stagger: {char.curstag}/{char.maxstag}, Health: {char.curhp}/{char.maxhp})"
            else:
                ret_str += f"\n{char.name} will revive in {char.deathtimer} acts. (Health: 0/{char.maxhp}) (Stagger: 0/{char.maxstag})"
        return ret_str

@dataclass
class Action:
    def __init__(self, speed:int, skill:Skill, att:Character, defn:Character, act_type: ActionType):
        self.speed = speed
        self.skill = skill
        self.att = att
        self.defn = defn
        self.act_type = act_type

class Skill:
    def __init__(self, baseval, coinnum, coinval, skill_type:str | SkillType):
        self.baseval = baseval
        self.coinnum = coinnum
        self.coinval = coinval
        self.skill_type: SkillType
        if isinstance(skill_type, str):
            self.skill_type = SkillType.from_str(skill_type)
        else:
            self.skill_type = skill_type

# Roll the skill cycle at the start of character init
def assign_skillcycle():
    integer_list = [1, 1, 1, 2, 2, 3]
    random.shuffle(integer_list)
    return integer_list

def get_player_input(characters: list[Character]):
    print("Choose which character to make an action:")
    for i, character in enumerate(characters, 1):
        if isinstance(character, BusCharacter):
            continue
        if character.is_stagger():
            print(f"{i-1}. {character.name} is staggered")
        elif character.is_alive():
            print(f"{i-1}. {character.name} (Speed: {character.speed})")
        else:
            print(f"{i-1}. {character.name} is dead (Timer: {character.deathtimer} turns)")
    choice = 0
    while True:
        try:
            choice = int(input("Enter the number of the character you want to attack with: "))
            if choice < 0 or choice > 3:
                print("Wrong input. Try again")
            elif not characters[choice].is_alive():
                print("Invalid input. The character can't make an action")
            elif characters[choice].is_stagger():
                print("Invalid input. The character is staggered")                
            elif choice == 0:
                print("Invalid choice, Mephistopheles can't make an action")
            else:
                break
        except ValueError:
            print("Invalid input. Please enter a valid integer.")
    return choice

def get_player_target(att_char: Character, enemy_chars: list[Character]):
    print(f"Choose which character for {att_char.name} to attack with speed of {att_char.speed}")
    for i, character in enumerate(enemy_chars, 1):
        if isinstance(character, BusCharacter):
            print(f"{i-1}. {character.name} (Health: {character.curhp})")
        elif character.is_alive():
            print(f"{i-1}. {character.name} (Speed: {character.speed})")
        else:
            print(f"{i-1}. {character.name} is dead (Timer: {character.deathtimer} turns)")
    choice = 0
    while True:
        try:
            choice = int(input("Enter the number of the character you want to attack: "))
            if choice < 0 or choice > 3:
                print(f"Wrong input. Try again")
            elif not enemy_chars[choice].is_alive():
                print(f"Invalid input. The target character is dead")
            else:
                break
        except ValueError:
            print("Invalid input. Please enter a valid integer.")
    return choice

def get_skill_choice(character: Character) -> int:
    print(f"Which skill do you want {character.name} to use?")
    skillnum1:int = character.skillcycle[0]
    skill1 = character.skills[skillnum1 - 1]
    print(f"1: S{skillnum1}, {skill1.baseval}+{skill1.coinval}*{skill1.coinnum}, Type: {skill1.skill_type}")
    skillnum2:int = character.skillcycle[1]
    skill2 = character.skills[skillnum2 - 1]
    print(f"2: S{skillnum2}, {skill2.baseval}+{skill2.coinval}*{skill2.coinnum}, Type: {skill2.skill_type}")
    choice = 0
    while True:
        try:
            choice = int(input("Enter the number of the skill slot you want to use: "))
            if choice < 1 or choice > 2:
                print(f"Wrong input. Try again")
            else:
                break
        except ValueError:
            print("Invalid input. Please enter a valid integer.")
    if choice == 1:
        return skillnum1
    else:
        return skillnum2

def check_game_end(p1team: list[Character], p1name: str, p2team: list[Character], p2name: str):
    if not p1team[0].is_alive:
        print(f"\n{p2name} wins!")
        sys.exit()
    elif not p2team[0].is_alive:
        print(f"\n{p1name} wins!")
        sys.exit()

def get_valid_input(prompt, valid_choices: list[int]):
    while True:
        user_input = input(prompt)
        try:
            choice = int(user_input)
            if choice in valid_choices:
                return choice
            print("Invalid choice. Please select a valid integer between 1 to 12.")
        except ValueError:
            print("Invalid input. Please enter an integer.")

def numbers_to_characters(number_list: list[int]):
    character_mapping = {
        0: BusCharacter(),
        1: Character("Yisang", 159, 24, 0, assign_skillcycle(), 4, 8, Resistance(2, 0.5, 1), (Skill(4, 1, 7, "slash"), Skill(4, 2, 4, "pierce"), Skill(6, 3, 2, "slash"))),
        2: Character("Faust", 186, 28, 0, assign_skillcycle(), 2, 4, Resistance(2, 0.5, 1), (Skill(4, 1, 7, "bash"), Skill(5, 2, 4, "bash"), Skill(7, 2, 2, "pierce"))),
        3: Character("Don Quixote", 146, 29, 0, assign_skillcycle(), 3, 6, Resistance(1, 0.5, 2), (Skill(4, 1, 7, "pierce"), Skill(4, 1, 12, "pierce"), Skill(3, 3, 3, "pierce"))),
        4: Character("Ryoshu", 146, 29, 0, assign_skillcycle(), 3, 6, Resistance(0.5, 1, 2), (Skill(4, 1, 7, "slash"), Skill(4, 2, 5, "slash"), Skill(5, 3, 3, "slash"))),
        5: Character("Meursault", 199, 40, 0, assign_skillcycle(), 2, 3, Resistance(1, 2, 0.5), (Skill(3, 2, 4, "bash"), Skill(6, 1, 9, "bash"), Skill(4, 4, 2, "bash"))),
        6: Character("Honglu", 146, 29, 0, assign_skillcycle(), 3, 6, Resistance(2, 1, 0.5), (Skill(4, 1, 7, "bash"), Skill(4, 2, 4, "slash"), Skill(6, 2, 4, "bash"))),
        7: Character("Heathcliff", 171, 26, 0, assign_skillcycle(), 2, 5, Resistance(2, 1, 0.5), (Skill(4, 1, 7, "bash"), Skill(4, 2, 4, "bash"), Skill(4, 2, 8, "bash"))),
        8: Character("Ishmael", 172, 50, 0, assign_skillcycle(), 5, 8, Resistance(2, 1, 0.5), (Skill(4, 1, 7, "bash"), Skill(6, 1, 9, "bash"), Skill(8, 1, 12, "bash"))),
        9: Character("Rodion", 172, 26, 0, assign_skillcycle(), 2, 5, Resistance(0.5, 2, 1), (Skill(4, 1, 7, "slash"), Skill(4, 2, 4, "slash"), Skill(4, 4, 2, "slash"))),
        10: Character("Sinclair", 132, 26, 0, assign_skillcycle(), 3, 7, Resistance(0.5, 2, 1), (Skill(4, 1, 7, "slash"), Skill(4, 3, 2, "slash"), Skill(5, 3, 3, "slash"))),
        11: Character("Outis", 132, 26, 0, assign_skillcycle(), 3, 7, Resistance(0.5, 1, 2), (Skill(3, 3, 2, "pierce"), Skill(5, 2, 4, "slash"), Skill(7, 1, 14, "pierce"))),
        12: Character("Gregor", 158, 47, 0, assign_skillcycle(), 3, 7, Resistance(1, 0.5, 2), (Skill(4, 1, 7, "slash"), Skill(5, 1, 10, "pierce"), Skill(6, 2, 4, "pierce"))),
    }

    character_list = [character_mapping[number] for number in number_list]
    return character_list

def print_board(actnum: int, p1team: Team, p2team: Team):
    print("\n" + "=" * 40)
    print(f"Act {actnum}")
    print("=" * 10)
    print(p1team)
    print("=" * 10)
    print(p2team)
    print("=" * 40)

action_list: list[Action] = []

def add_action(action: Action):
    global action_list
    att_exists = False

    # Check if there's an element with the same att
    for i, existing_action in enumerate(action_list):
        if existing_action.att.name == action.att.name:
            action_list[i] = action  # Replace existing action with the new one
            att_exists = True
            break

    # If no existing att, find the correct position based on speed and insert
    if not att_exists:
        added = False
        for i, existing_action in enumerate(action_list):
            if action.speed > existing_action.speed:
                action_list.insert(i, action)
                added = True
                break
        if not added:
            action_list.append(action)

def remove_all_actions():
    global action_list
    action_list = []

def find_and_remove_action_by_att(defender: Character):
    global action_list
    found_action = None
    
    for i, action in enumerate(action_list):
        if action.att.name == defender.name:
            found_action = action
            del action_list[i]
            break
    
    return found_action

def calculate_damage(attacker: Character, attack_skill: Skill, defender: Character, coin_lost: int):
    coin_count = attack_skill.coinnum
    coin_val = attack_skill.coinval
    coin_base = attack_skill.baseval
    prob = attacker.sanity + 50
    dmg_val = coin_base
    coin_num = coin_lost
    while coin_count > coin_num:
        coin_num += 1
        dmg_ratio = defender.find_mult(attack_skill.skill_type)
        print(f"Toss the coin #{coin_num}")
        time.sleep(0.5)
        chance = random.randint(0,99)
        if chance < prob:
            print(f"Coin is on head")
            dmg_val += coin_val
        else:
            print(f"Coin is on tail")
        time.sleep(0.5)
        damage = int(dmg_val * dmg_ratio)
        print(f"{attacker.name} dealt {damage} damage to {defender.name}")
        defender.take_damage(damage)
        time.sleep(0.5)
        if not defender.is_alive():
            coin_count = 0
            if isinstance(defender, BusCharacter):
                print(f"Game is over.")
                sys.exit()

def clash(attacker: Character, attack_skill: Skill, defender: Character, defend_skill: Skill):
    clash_num = 0
    att_coin_count = attack_skill.coinnum
    defn_coin_count = defend_skill.coinnum
    att_coin_val = attack_skill.coinval
    att_coin_base = attack_skill.baseval
    att_prob = attacker.sanity + 50
    defn_coin_val = defend_skill.coinval
    defn_coin_base = defend_skill.baseval
    defn_prob = defender.sanity + 50
    att_coin_lost = 0
    defn_coin_lost = 0
    while att_coin_count > att_coin_lost and defn_coin_count > defn_coin_lost:
        clash_num += 1
        att_val = att_coin_base
        defn_val = defn_coin_base
        att_coin_num = att_coin_lost
        defn_coin_num = defn_coin_lost
        while att_coin_count > att_coin_num:
            att_coin_num += 1
            chance = random.randint(0,99)
            if chance < att_prob:
                att_val += att_coin_val
        while defn_coin_count > defn_coin_num:
            defn_coin_num += 1
            chance = random.randint(0,99)
            if chance < defn_prob:
                defn_val += defn_coin_val
        if att_val > defn_val:
            print(f"Clash #{clash_num}, {att_val}:{defn_val}. {defender.name} lost a coin.")
            defn_coin_lost += 1
            time.sleep(0.25)
        elif defn_val > att_val:
            print(f"Clash #{clash_num}, {att_val}:{defn_val}. {attacker.name} lost a coin.")
            att_coin_lost += 1
            time.sleep(0.25)
        else:
            print(f"Clash #{clash_num}, {att_val}:{defn_val}. It's even.")
            time.sleep(0.25)
            continue
    if defn_coin_count == defn_coin_lost:
        san_heal = 10+clash_num
        attacker.sanity += san_heal
        print(f"{attacker.name} won the clash, restores {san_heal} sanity and starts attacking {defender.name}")
        time.sleep(0.5)
        calculate_damage(attacker, attack_skill, defender, att_coin_lost)
    if att_coin_count == att_coin_lost:
        san_heal = 10*(1+0.1*clash_num)
        defender.sanity += san_heal
        print(f"{defender.name} won the clash, restores {san_heal} sanity and starts attacking {attacker.name}")
        time.sleep(0.5)
        calculate_damage(defender, defend_skill, attacker, defn_coin_lost)

def turn_action(act: int, player: Team, enemy: Team):
    print_board(act, player, enemy)
    print(f"{player.name}, it's your turn.")
    turn_end = False
    while not turn_end:
        user_input = input("What do you want to do? Press 0 to make action, 1 to see the board, 2 to end turn, q to quit the game: ")
        if user_input == "0":
            player_choice = get_player_input(player.characters)
            attacking_character = player.characters[player_choice]
            skill_choice = get_skill_choice(attacking_character)
            target_choice = get_player_target(attacking_character, enemy.characters)
            target_character = enemy.characters[target_choice]
            clash_opt = attacking_character.target(target_character, skill_choice)
            skill = attacking_character.skills[skill_choice - 1]
            action = Action(attacking_character.speed, skill, attacking_character, target_character, clash_opt)
            add_action(action)
        elif user_input == "1":
            print_board(act, player, enemy)
        elif user_input == "2":
            turn_end = True
        elif user_input == "q":
            sys.exit()
        else:
            print("Invalid Input")

def main():
    # Get the player name and create a team of limbus ID to defend mephistopheles 
    print("Welcome to the Limbus Company pvp battle")
    print("Let's start with the name of player 1: ")
    p1name = input()
    print("Player 1's name is " + p1name + ".")
    print("Please enter the name of player 2: ")
    p2name = input()
    print("Player 2's name is " + p2name + ".")

    all_numbers = list(range(1, 13))
    chosen_numbers = []
    for _ in range(6):
        if len(chosen_numbers) in (0, 3, 4):
            prompt = f"{p1name}, pick a number from 1 to 12 to add to your team: "
        if len(chosen_numbers) in (1, 2, 5):
            prompt = f"{p2name}, pick a number from 1 to 12 to add to your team: "
        valid_choices = [num for num in all_numbers if num not in chosen_numbers]
        choice = get_valid_input(prompt, valid_choices)
        chosen_numbers.append(choice)
    list1 = [0, chosen_numbers[0], chosen_numbers[3], chosen_numbers[4]]
    list2 = [0, chosen_numbers[1], chosen_numbers[2], chosen_numbers[5]]
    p1team = Team(p1name, numbers_to_characters(list1))
    p2team = Team(p2name, numbers_to_characters(list2))
    
    act = 0
    current_player = 1
    while True:
        act += 1
        for character in chain(p1team.characters, p2team.characters):
            character.next_turn()
        #Reduce death timer and bring back alive

        # Get player input and perform the attack
        turn_action(act, p1team, p2team)
        turn_action(act, p2team, p1team)

        # Start the battle phase
        while len(action_list) > 0:
            attack_action = action_list[0]
            if attack_action.act_type == ActionType.CLASH:
                defend_action = find_and_remove_action_by_att(attack_action.defn)
                if defend_action is None:
                    if attack_action.defn.is_alive():
                        print(f"{attack_action.att.name} is attacking {attack_action.defn.name} one-sided")
                        time.sleep(0.5)
                        calculate_damage(attack_action.att, attack_action.skill, attack_action.defn, 0)
                        time.sleep(0.5)
                    del action_list[0]
                else:
                    print(f"{attack_action.att.name} begin clash against {attack_action.defn.name}")
                    time.sleep(0.5)
                    if not defend_action.att.is_stagger():
                        clash(attack_action.att, attack_action.skill, defend_action.att, defend_action.skill)
                        time.sleep(0.5)
                    elif defend_action.att.is_alive():
                        print(f"{attack_action.att.name} is attacking staggered {attack_action.defn.name}")
                        time.sleep(0.5)
                        calculate_damage(attack_action.att, attack_action.skill, attack_action.defn, 0)
                        time.sleep(0.5)
                    else:
                        print(f"{attack_action.defn.name} is already dead")
                        time.sleep(0.5)
                    del action_list[0]
            else:
                if attack_action.defn.is_alive():
                    print(f"{attack_action.att.name} is attacking {attack_action.defn.name} one-sided")
                    time.sleep(0.5)
                    calculate_damage(attack_action.att, attack_action.skill, attack_action.defn, 0)
                    time.sleep(0.5)
                else:
                    print(f"{attack_action.defn.name} is already dead")
                del action_list[0]

if __name__ == "__main__":
    main()
