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
    def of_type(self, skill_type: SkillType) -> float:
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

    def coin_toss(self) -> bool:
        #True: head / False: tail
        return random.randint(0,99) < 50 + self.sanity

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
        return self.resistance.of_type(skill_type)
    
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
    
    def __repr__(self) -> str:
        if not self.is_alive():
            return f"{self.name} will revive in {self.deathtimer} acts. (Health: 0/{self.maxhp}) (Stagger: 0/{self.maxstag})"
        if self.is_stagger():
            return f"{self.name} is staggered \n (Speed: 0, Sanity: {self.sanity}, Stagger: {self.curstag}/{self.maxstag}, Health: {self.curhp}/{self.maxhp})"
        return f"{self.name} \n (Speed: {self.speed}, Sanity: {self.sanity}, Skill: (S{self.skillcycle[0]}/S{self.skillcycle[1]}), Stagger: {self.curstag}/{self.maxstag}, Health: {self.curhp}/{self.maxhp})"

    
    def basic_info(self) -> str:
        if not self.is_alive():
            return f"{self.name} is dead (Timer: {self.deathtimer} turns)"
        if self.is_stagger():
            return f"{self.name} is staggered"
        return f"{self.name} (Speed: {self.speed})"

    def user_select_skill(self) -> int:
        print(f"Which skill do you want {self.name} to use?")
        print(f"1: S{self.skillcycle[0]}, {self.skills[self.skillcycle[0] - 1]}")
        print(f"2: S{self.skillcycle[1]}, {self.skills[self.skillcycle[1] - 1]}")
        choice = 0
        while True:
            try:
                choice = int(input("Enter the number of the skill slot you want to use: "))
                if choice < 1 or choice > 2:
                    print("Wrong input. Try again")
                else:
                    break
            except ValueError:
                print("Invalid input. Please enter a valid integer.")
        return self.skillcycle[choice - 1]

    def user_select_target(self, enemy_team: Team) -> int:
        print(f"Choose which character for {self.name} to attack with speed of {self.speed}")
        enemy_chars = enemy_team.characters
        for i, character in enumerate(enemy_chars, 1):
            print(f"{i - 1}. {character.basic_info()}")
        choice = 0
        while True:
            try:
                choice = int(input("Enter the number of the character you want to attack: "))
                if choice < 0 or choice > 3:
                    print("Wrong input. Try again")
                elif not enemy_chars[choice].is_alive():
                    print("Invalid input. The target character is dead")
                else:
                    break
            except ValueError:
                print("Invalid input. Please enter a valid integer.")
        return choice
    
class BusCharacter(Character):
    def __init__(self):
        super().__init__("Mephistopheles", 50, 100, 0, assign_skillcycle(), 0, 0, Resistance(1, 1, 1), (Skill(0,0,0,"slash"), Skill(0,0,0,"slash"), Skill(0,0,0,"slash")))

    def next_turn(self):
        pass

    def __repr__(self) -> str:
        return f"{self.name} (Health: {self.curhp}/{self.maxhp})"

    def basic_info(self) -> str:
        return f"{self.name} (Health: {self.curhp})"
    
class Team:
    def __init__(self, name: str, characters: list[Character]):
        self.name = name
        self.characters = characters

    def __repr__(self) -> str:
        ret_str = f"{self.name}'s Team"
        for char in self.characters:
            if isinstance(char, BusCharacter):
                ret_str += f"\n{self.name}'s {char})"
            else:
                ret_str += f"\n{char}"
        return ret_str

@dataclass
class Action:
    speed: int
    skill: Skill
    att: Character
    defn: Character
    act_type: ActionType

    def _is_clash(self, defending_action: Action | None = None):
        return self.act_type == ActionType.CLASH and defending_action is not None and not self.defn.is_stagger()

    def battle(self, defending_action: Action | None = None):
        assert defending_action is None or defending_action.att == self.defn
        if not self.defn.is_alive():
            return
        if self._is_clash(defending_action):
            self.clash(defending_action)
            return
        self.one_side_attack()

    def one_side_attack(self, coin_lost:int=0):
        coin_count = self.skill.coinnum
        coin_val = self.skill.coinval
        coin_base = self.skill.baseval
        dmg_val = coin_base
        coin_num = coin_lost
        while coin_count > coin_num:
            coin_num += 1
            dmg_ratio = self.defn.find_mult(self.skill.skill_type)
            print(f"Toss the coin #{coin_num}")
            time.sleep(0.5)
            if self.att.coin_toss():
                print("Coin is on head")
                dmg_val += coin_val
            else:
                print("Coin is on tail")
            time.sleep(0.5)
            damage = int(dmg_val * dmg_ratio)
            print(f"{self.att.name} dealt {damage} damage to {self.defn.name}")
            self.defn.take_damage(damage)
            time.sleep(0.5)
            if not self.defn.is_alive():
                coin_count = 0
                if isinstance(self.defn, BusCharacter):
                    print("Game is over.")
                    sys.exit()

    def clash(self, defend_action: Action):
        clash_num = 0
        att_coin_count = self.skill.coinnum
        defn_coin_count = defend_action.skill.coinnum
        att_coin_val = self.skill.coinval
        att_coin_base = self.skill.baseval
        defn_coin_val = defend_action.skill.coinval
        defn_coin_base = defend_action.skill.baseval
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
                if self.att.coin_toss():
                    att_val += att_coin_val
            while defn_coin_count > defn_coin_num:
                defn_coin_num += 1
                if self.defn.coin_toss():
                    defn_val += defn_coin_val
            if att_val > defn_val:
                print(f"Clash #{clash_num}, {att_val}:{defn_val}. {self.defn.name} lost a coin.")
                defn_coin_lost += 1
                time.sleep(0.25)
            elif defn_val > att_val:
                print(f"Clash #{clash_num}, {att_val}:{defn_val}. {self.att.name} lost a coin.")
                att_coin_lost += 1
                time.sleep(0.25)
            else:
                print(f"Clash #{clash_num}, {att_val}:{defn_val}. It's even.")
                time.sleep(0.25)
                continue
        if defn_coin_count == defn_coin_lost:
            san_heal = 10+clash_num
            self.att.sanity += san_heal
            print(f"{self.att.name} won the clash, restores {san_heal} sanity and starts attacking {self.defn.name}")
            time.sleep(0.5)
            self.one_side_attack(att_coin_lost)
        if att_coin_count == att_coin_lost:
            san_heal = 10 + clash_num
            self.defn.sanity += san_heal
            print(f"{self.defn.name} won the clash, restores {san_heal} sanity and starts attacking {self.att.name}")
            time.sleep(0.5)
            defend_action.one_side_attack(defn_coin_lost)

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

    def __repr__(self):
        return f"{self.baseval}+{self.coinval}*{self.coinnum}, Type: {self.skill_type.name}"

# Roll the skill cycle at the start of character init
def assign_skillcycle():
    integer_list = [1, 1, 1, 2, 2, 3]
    random.shuffle(integer_list)
    return integer_list





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

# action_list: list[Action] = []

class ActionList:
    def __init__(self):
        self.action_list: list[Action] = []

    def add_action(self, action: Action):
        # Check if there's an element with the same att
        for i, existing_action in enumerate(self.action_list):
            if existing_action.att.name == action.att.name:
                self.action_list[i] = action  # Replace existing action with the new one
                return

        # If no existing att, find the correct position based on speed and insert
        for i, existing_action in enumerate(self.action_list):
            if action.speed > existing_action.speed:
                self.action_list.insert(i, action)
                break
        else:
            self.action_list.append(action)

    def remove_all_actions(self):
        self.action_list = []

    def find_and_remove_action_by_att(self, defender: Character):
        found_action = None

        for i, action in enumerate(self.action_list):
            if action.att.name == defender.name:
                found_action = action
                del self.action_list[i]
                return found_action

        return None
    
    def __len__(self) -> int:
        return len(self.action_list)
    
    def get_top_and_remove(self) -> Action:
        return self.action_list.pop(0)

class GameManager:
    def __init__(self, action_list: ActionList, team1:Team, team2:Team):
        self.action_list = action_list
        self.player = team1
        self.enemy = team2
        self.act:int = 0

    def __repr__(self) -> str:
        ret_str = "=" * 40
        ret_str += f"\nAct {self.act}"
        ret_str += "\n" + "=" * 10
        ret_str += f"\n{self.player}"
        ret_str += "\n" + "=" * 10
        ret_str += f"\n{self.enemy}"
        ret_str += "\n" + "=" * 40
        return ret_str

    def change_side(self):
        self.player, self.enemy = self.enemy, self.player

    def _user_select_character(self) -> int:
        print("Choose which character to make an action:")
        characters = self.player.characters
        for i, character in enumerate(characters, 1):
            if isinstance(character, BusCharacter):
                continue
            print(f"{i - 1}. {character.basic_info()}")
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

    def _user_make_action(self):
        character_choice = self._user_select_character()
        attacking_character = self.player.characters[character_choice]
    
        skill_choice = attacking_character.user_select_skill()
    
        target_choice = attacking_character.user_select_target(self.enemy)
        target_character = self.enemy.characters[target_choice]
    
        clash_opt = attacking_character.target(target_character, skill_choice)
        skill = attacking_character.skills[skill_choice - 1]
        action = Action(attacking_character.speed, skill, attacking_character, target_character, clash_opt)
        self.action_list.add_action(action)

    def user_turn(self):
        print(self)
        print(f"{self.player.name}, it's your turn.")
        while True:
            user_input = input("What do you want to do? Press 0 to make action, 1 to see the board, 2 to end turn, q to quit the game: ")
            if user_input == "0":
                self._user_make_action()
            elif user_input == "1":
                print(self)
            elif user_input == "2":
                break
            elif user_input == "q":
                sys.exit()
            else:
                print("Invalid Input")

    def next_turn(self):
        self.act += 1
        for character in chain(self.player.characters, self.enemy.characters):
            character.next_turn()

    def resolve_action(self):
        while len(self.action_list) > 0:
            attack_action = self.action_list.get_top_and_remove()
            defend_action = None
            if attack_action.act_type == ActionType.CLASH:
                defend_action = self.action_list.find_and_remove_action_by_att(attack_action.defn)
                if defend_action is None:
                    if attack_action.defn.is_alive():
                        print(f"{attack_action.att.name} is attacking {attack_action.defn.name} one-sided")
                        time.sleep(0.5)
                else:
                    print(f"{attack_action.att.name} begin clash against {attack_action.defn.name}")
                    time.sleep(0.5)
                    if not defend_action.att.is_alive():
                        print(f"{attack_action.defn.name} is already dead")
                        time.sleep(0.5)
                    elif defend_action.att.is_stagger():
                        print(f"{attack_action.att.name} is attacking staggered {attack_action.defn.name}")
                        time.sleep(0.5)
            else:
                if attack_action.defn.is_alive():
                    print(f"{attack_action.att.name} is attacking {attack_action.defn.name} one-sided")
                    time.sleep(0.5)
                else:
                    print(f"{attack_action.defn.name} is already dead")
            attack_action.battle(defend_action)

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

    manager = GameManager(ActionList(), p1team, p2team)

    while True:
        #Reduce death timer and bring back alive
        manager.next_turn()

        # Get player input and perform the attack
        manager.user_turn()
        manager.change_side()
        manager.user_turn()
        manager.change_side()

        # Start the battle phase
        manager.resolve_action()

if __name__ == "__main__":
    main()
