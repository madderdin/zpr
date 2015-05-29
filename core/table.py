import threading
import socket
import select
import controller
import time
from game.game import Game


class Table(threading.Thread):
    """
        class responsible for adding, removing players at table
        implements connection between players and game
        implements observer pattern
    """
    PLAYERS_LIMIT = 3
    PLAYERS_MINIMUM = 2

    def __init__(self):
        threading.Thread.__init__(self)
        self.players = []
        self.players_sockets = []
        self.started = False
        self.controller = controller.Controller(self)
        self.game = Game(self)

    def run(self):
        """
            waits until enough players entered game and all of them are ready
            then starts main game loop
        :return: nothing
        """
        while not self.started:
            players_with_ready_input = self.__select_players()
            for player in players_with_ready_input:
                message = player.get_input()
                self.controller.serve_event(player, message['content'])

        self.game.game_loop()
        print 'Game ended'

    def add_player(self, player):
        """
            adds observer
            raises exception if number of players limit was reached
        :param player: Player
        :raise: Exception
        :return: nothing
        """
        if len(self.players) < self.PLAYERS_LIMIT:
            self.players.append(player)
            self.players_sockets.append(player.socket)
            self.notify_players()
        else:
            raise Exception('Players limit reached.\n')

    def remove_player(self, player):
        """
            remove observer
            raise exception if given player does not exist
        :param player: Player
        :raise: Exception
        :return: nothing
        """
        if player in self.players:
            self.players.remove(player)
            self.players_sockets.remove(player.socket)
            self.notify_players()
        else:
            raise Exception('No such player at the table.\n')

    def notify_players(self):
        """
            notify observers
            sends message to all players containing game state
        :return: nothing
        """
        time.sleep(1)
        for player in self.players:
            try:
                player.send(self.__dict(player))
            except socket.error:
                controller.pressed_leave(self, player)
                print 'Player ' + player.name + ' disconnected'

    def is_full(self):
        """
            checks if number of players has been reached
        :return: boolean
        """
        return len(self.players) == self.PLAYERS_LIMIT

    def is_empty(self):
        """
            checks if number of players equals zero
        :return: boolean
        """
        return len(self.players) == 0

    def __select_players(self):
        """
            timeout is set on 2 seconds, it means that every player whose socket
            received input before calling this method or during timeout will be placed in return list
        :return: list of Player
        """
        timeout = 2.0
        input_ready, output_ready, except_ready = select.select(self.players_sockets, [], [], timeout)

        players_with_ready_input = []
        for ready_socket in input_ready:
            for player in self.players:
                if ready_socket is player.socket:
                    players_with_ready_input.append(player)
                    break

        return players_with_ready_input

    def __dict(self, player):
        """
            method creates dictionary containing all information about game state, all players and given player cards
            keys: 'players_number', 'first_card', 'second_card', '0', '1', ... 'n' (depends on players number)
            'table_card_0', ... , 'table_card_4', 'dealer'
        :param player: Player
        :return: dictionary
        """
        dictionary = {
            'players_number': len(self.players),
            'first_card': str(player.hand.firstCard),
            'second_card': str(player.hand.secondCard),
        }

        i = 0
        while i < len(self.players):
            dictionary[i] = self.players[i].info()
            i += 1

        i = 0
        while i < 5:
            dictionary['table_card_' + str(i)] = 'None'
            if i < len(self.game.tableCards):
                dictionary['table_card_' + str(i)] = str(self.game.tableCards[i])
            i += 1

        if self.game.dealer is not None:
            dictionary['dealer'] = self.players.index(self.game.dealer)
        else:
            dictionary['dealer'] = None

        return dictionary