package database

import (
	"errors"
	"fmt"
	"kth_activities_helper/internal/calculation"
	"kth_activities_helper/internal/config"
	"kth_activities_helper/internal/models"
	"log/slog"
	"net/http"
	"strconv"
	"strings"
	"time"

	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

type Storage struct {
	db *gorm.DB
}

func createConnectionString() string {
	return "host=" + config.AppConfig.DatabaseConfig.Address +
		" user=" + config.AppConfig.DatabaseConfig.User +
		" password=" + config.AppConfig.DatabaseConfig.Pass +
		" dbname=" + config.AppConfig.DatabaseConfig.Database +
		" port=" + strconv.Itoa(config.AppConfig.DatabaseConfig.Port) +
		" sslmode=" + config.AppConfig.DatabaseConfig.SSLmode
}

func New(log *slog.Logger) (*Storage, error) {
	dsn := createConnectionString()
	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})
	if err != nil {
		log.Error("Failed to connect to database", err.Error())
		return nil, err
	}
	err = db.AutoMigrate(&models.MatchType{}, &models.Matches{}, &models.User{}, &models.MatchUserScrim{}, &models.Role{})
	if err != nil {
		log.Error("Failed to auto migrate", err.Error())
		return nil, err
	}
	log.Info("Successfully connected to database")
	storage := &Storage{db: db}
	return storage, nil
}

//MatchTypeRepository

func (storage *Storage) SelectMatchTypes() ([]models.MatchType, error) {
	var matchTypes []models.MatchType
	result := storage.db.Find(&matchTypes)
	if result.Error != nil {
		return nil, result.Error
	}
	return matchTypes, nil
}

func (storage *Storage) CreateMatchType(matchTypeName string) (uint64, error) {
	matchTypeToCreate := models.MatchType{Name: matchTypeName}
	result := storage.db.Create(&matchTypeToCreate)
	if result.Error != nil {
		return 0, result.Error
	}

	return matchTypeToCreate.ID, nil
}

//MatchRepository

func (storage *Storage) SelectMatches() ([]models.Matches, error) {
	matches := []models.Matches{}

	result := storage.db.Preload("MatchUserScrim.Player").Find(&matches) // TODO: возможно убрать Preload так как потом будет нагружать сервак
	if result.Error != nil {
		return nil, result.Error
	}
	return matches, nil
}

func (storage *Storage) SelectOneMatch(id uint64) (models.Matches, error) {
	match := models.Matches{}
	result := storage.db.Preload("MatchUserScrim").Preload("MatchType").First(&match, id)
	if result.Error != nil {
		return models.Matches{}, result.Error
	}
	return match, nil
}

func (storage *Storage) CreateMatch(osuMatchId uint64, matchTypeId uint64, matchDate time.Time) (uint64, error) {
	matchToCreate := models.Matches{MatchOsuID: osuMatchId, MatchTypeId: matchTypeId, Date: matchDate}
	result := storage.db.Create(&matchToCreate)
	if result.Error != nil {
		return 0, result.Error
	}
	return matchToCreate.Id, nil
}

func (storage *Storage) EditMatchOld(matchId uint64, matchTypeId uint64, matchDate time.Time, isApproved bool) (models.Matches, error) {
	match := models.Matches{}
	result := storage.db.First(&match, matchId)
	if result.Error != nil {
		return models.Matches{}, result.Error
	}
	match.MatchTypeId = matchTypeId
	match.Date = matchDate
	match.IsApproved = isApproved
	result = storage.db.Save(&match)
	if result.Error != nil {
		return models.Matches{}, result.Error
	}
	return match, nil
}

func (storage *Storage) EditMatchScrim(matchId uint64, matchDate time.Time, firstPlayerId uint64,
	firstPlayerScore uint64, secondPlayerId uint64, secondPlayerScore uint64) (models.Matches, error) {
	match := models.Matches{}
	result := storage.db.Preload("MatchUserScrim").First(&match, matchId)
	if result.Error != nil {
		return models.Matches{}, result.Error
	}
	if len(match.MatchUserScrim) == 2 {
		if match.MatchUserScrim[0].PlayerId == firstPlayerId && match.MatchUserScrim[1].PlayerId == secondPlayerId {
			match.MatchUserScrim[0].Score = firstPlayerScore
			match.MatchUserScrim[1].Score = secondPlayerScore
		} else if match.MatchUserScrim[0].PlayerId == secondPlayerId && match.MatchUserScrim[1].PlayerId == firstPlayerId {
			match.MatchUserScrim[0].Score = secondPlayerScore
			match.MatchUserScrim[1].Score = firstPlayerScore
		} else {
			return models.Matches{}, errors.New("Players id mismatch !")
		}
	}
	match.Date = matchDate
	result = storage.db.Save(&match) // TODO: чекнуть, сохраняются ли скоры
	/* transactionRes := storage.db.Transaction(func(tx *gorm.DB) error {
		if err := tx.Save(&m).Error; err != nil {
			return err
		}
		if err := tx.Delete(&match).Error; err != nil {
			return err
		}
		return nil
	})
	// result = storage.db.Delete(&match)
	if transactionRes != nil {
		return false, transactionRes
	}*/
	// match.MatchTypeId = matchTypeId

	if result.Error != nil {
		return models.Matches{}, result.Error
	}
	return match, nil
}

func (storage *Storage) DeleteMatch(matchId uint64) (bool, error) {
	match := models.Matches{}
	result := storage.db.Preload("MatchUserScrim").First(&match, matchId)
	if result.Error != nil {
		return false, result.Error
	}
	if match.IsApproved {
		return false, errors.New("The match is approved")
	}
	var matchesUserScrim []models.MatchUserScrim
	matchesUserScrim = match.MatchUserScrim
	// result = storage.db.Find(&matchesUserScrim)
	transactionRes := storage.db.Transaction(func(tx *gorm.DB) error {
		if err := tx.Delete(&matchesUserScrim).Error; err != nil {
			return err
		}
		if err := tx.Delete(&match).Error; err != nil {
			return err
		}
		return nil
	})
	// result = storage.db.Delete(&match)
	if transactionRes != nil {
		return false, transactionRes
	}
	return true, nil
}

func (storage *Storage) ApproveMatch(matchId uint64) (models.Matches, error) {
	match := models.Matches{}
	result := storage.db.Preload("MatchUserScrim").Preload("MatchType").First(&match, matchId)
	if result.Error != nil {
		return models.Matches{}, result.Error
	}
	if match.IsApproved {
		return match, errors.New("match already approved")
	}
	if match.MatchType.Name != "scrim" {
		return match, nil // TODO: do match cost someday
	}
	var matchUsersScrims []models.MatchUserScrim
	test := storage.db.Preload("Player").Where(models.MatchUserScrim{MatchId: match.Id}).Find(&matchUsersScrims)
	if test.Error != nil {
		return match, test.Error
	}
	if len(matchUsersScrims) != 2 {
		return match, errors.New("match does not have two users scrims")
	}
	firstPlayerNewRating := calculation.GetNewRating(float64(matchUsersScrims[0].Player.Rating),
		float64(matchUsersScrims[1].Player.Rating),
		int(matchUsersScrims[0].Score),
		int(matchUsersScrims[1].Score))
	secondPlayerNewRating := calculation.GetNewRating(float64(matchUsersScrims[1].Player.Rating),
		float64(matchUsersScrims[0].Player.Rating),
		int(matchUsersScrims[1].Score),
		int(matchUsersScrims[0].Score))
	firstPlayerRatingChange := firstPlayerNewRating - float64(matchUsersScrims[0].Player.Rating)
	secondPlayerRatingChange := secondPlayerNewRating - float64(matchUsersScrims[1].Player.Rating)

	matchUsersScrims[0].RatingChange = firstPlayerRatingChange
	matchUsersScrims[1].RatingChange = secondPlayerRatingChange
	matchUsersScrims[0].Player.Rating = uint32(firstPlayerNewRating)
	matchUsersScrims[1].Player.Rating = uint32(secondPlayerNewRating)
	match.IsApproved = true
	transactionRes := storage.db.Transaction(func(tx *gorm.DB) error {

		if err := tx.Save(&matchUsersScrims[0]).Error; err != nil {
			return err
		}
		if err := tx.Save(&matchUsersScrims[1]).Error; err != nil {
			return err
		}
		if err := tx.Save(&matchUsersScrims[0].Player).Error; err != nil {
			return err
		}
		if err := tx.Save(&matchUsersScrims[1].Player).Error; err != nil {
			return err
		}
		if err := tx.Save(&match).Error; err != nil {
			return err
		}
		return nil
	})
	if transactionRes.Error != nil {
		return match, errors.New("transaction failed")
	}
	return match, nil
}

// UserRepository

func (storage *Storage) SelectUsers() ([]models.User, error) {
	users := []models.User{}
	result := storage.db.Find(&users)
	if result.Error != nil {
		return nil, result.Error
	}
	return users, nil
}

func (storage *Storage) SelectOneUser(osuId uint64) (models.User, error) {
	user := models.User{}
	result := storage.db.Preload("MatchUserScrim").First(&user, osuId)
	if result.Error != nil {
		return models.User{}, result.Error
	}
	return user, nil
}

func (storage *Storage) SelectOneUserByUsername(username string) (models.User, error) {
	user := models.User{}
	result := storage.db.Preload("MatchUserScrim").Where(models.User{Username: username}).First(&user)
	if result.Error != nil {
		return models.User{}, result.Error
	}
	return user, nil
}

func (storage *Storage) CreateUser(osuId uint64, discordId uint64, rating uint32, username string, active bool) (uint64, error) {
	userToCreate := models.User{OsuId: osuId, DiscordId: discordId, Rating: rating, Username: username, Active: active}
	result := storage.db.Create(&userToCreate)
	if result.Error != nil {
		return 0, result.Error
	}
	return userToCreate.OsuId, nil
}

func (storage *Storage) EditUser(osuId uint64, discordId uint64, rating uint32, username string, active bool) (models.User, error) {
	user := models.User{}
	result := storage.db.First(&user, osuId)
	if result.Error != nil {
		return models.User{}, result.Error
	}
	user.DiscordId = discordId
	user.Rating = rating
	user.Username = username
	user.Active = active
	result = storage.db.Save(&user)
	if result.Error != nil {
		return models.User{}, result.Error
	}
	return user, nil
}
func (storage *Storage) SelectMatchUserScrims() ([]models.MatchUserScrim, error) {
	matchUserScrims := []models.MatchUserScrim{}
	result := storage.db.Preload("Player").Preload("Match").Find(&matchUserScrims)
	if result.Error != nil {
		return nil, result.Error
	}
	return matchUserScrims, nil
}
func (storage *Storage) CreateMatchUserScrim(playerId uint64, matchId uint64, score uint64, isBlue bool, ratingChange float64) (uint64, uint64, error) {
	matchUserScrimToCreate := models.MatchUserScrim{PlayerId: playerId, MatchId: matchId, Score: score, IsBlue: isBlue,
		RatingChange: ratingChange}
	result := storage.db.Create(&matchUserScrimToCreate)
	if result.Error != nil {
		return 0, 0, result.Error
	}
	return matchUserScrimToCreate.PlayerId, matchUserScrimToCreate.MatchId, nil
}

// ______________________________________________
type Player struct {
	Nickname  string
	OsuID     uint64
	Rating    int
	Active    bool
	Matches   []Match
	DiscordID string
}

type Match struct {
	FirstPlayerID  uint64
	SecondPlayerID uint64
}

type Response struct {
	PairsNickname []string   `json:"pairs_nickname"`
	PairsDiscord  []string   `json:"pairs_discord"`
	Unused        []string   `json:"unused"`
	PairsRow      []string   `json:"pairs_row"`
	CreatedPairs  [][]string `json:"created_pairs,omitempty"` // Add this field for created pairs

}

func (storage *Storage) CreatePairs(r *http.Request) (Response, int, error) {
	var response Response
	usedPlayers := make(map[string]struct{})
	pairs := []struct {
		FirstPlayer  models.User
		SecondPlayer models.User
	}{}

	var pairsCorrectionList []string
	// Uncomment if you need to decode pairsCorrectionList from the request body
	/*
		if err := json.NewDecoder(r.Body).Decode(&pairsCorrectionList); err != nil {
			return response, http.StatusBadRequest, fmt.Errorf("failed to decode request body: %v", err)
		}
	*/

	var players []models.User
	if err := storage.db.Where("active = ?", true).Order("rating DESC").Find(&players).Error; err != nil {
		return response, http.StatusInternalServerError, err
	}

	if len(pairsCorrectionList) > 0 {
		for _, pair := range pairsCorrectionList {
			playerNames := strings.Split(pair, ",")
			if len(playerNames) < 2 {
				continue
			}
			firstPlayerName := strings.TrimSpace(playerNames[0])
			secondPlayerName := strings.TrimSpace(playerNames[1])

			firstPlayer, err := storage.SelectOneUserByUsername(firstPlayerName)
			if err != nil {
				return response, http.StatusNotFound, fmt.Errorf("the player with nickname %s is not found", firstPlayerName)
			}
			secondPlayer, err := storage.SelectOneUserByUsername(secondPlayerName)
			if err != nil {
				return response, http.StatusNotFound, fmt.Errorf("the player with nickname %s is not found", secondPlayerName)
			}

			usedPlayers[firstPlayer.Username] = struct{}{}
			usedPlayers[secondPlayer.Username] = struct{}{}
			pairs = append(pairs, struct {
				FirstPlayer  models.User
				SecondPlayer models.User
			}{FirstPlayer: firstPlayer, SecondPlayer: secondPlayer})
		}
	}

	allPlayersSet := make(map[string]struct{})
	for _, player := range players {
		allPlayersSet[player.Username] = struct{}{}
	}

	unused := []string{}
	oneYearAgo := time.Now().AddDate(-1, 0, 0)
	for i := 0; i < len(players); i++ {
		player := players[i]

		if _, used := usedPlayers[player.Username]; used {
			continue
		}

		for j := i + 1; j < len(players); j++ {
			opponent := players[j]

			if opponent.OsuId == player.OsuId {
				continue
			}

			if _, used := usedPlayers[opponent.Username]; used {
				continue
			}

			if player.Rating-opponent.Rating > 300 {
				unused = append(unused,
					fmt.Sprintf("Cannot find a decent opponent for: %s (rating %d)", player.Username, player.Rating))
				usedPlayers[player.Username] = struct{}{}
				break
			}

			matches := []models.MatchUserScrim{}
			if err := storage.db.Where("match_id IN (SELECT id FROM matches WHERE id IN (SELECT match_id FROM match_user_scrims WHERE player_id = ?) AND date > ?)", player.OsuId, oneYearAgo.Format("2006-01-02 15:04:05")).Find(&matches).Error; err != nil {
				return response, http.StatusInternalServerError, err
			}

			skipMatchCheck := false
			for _, match := range matches {
				if match.PlayerId == opponent.OsuId {
					skipMatchCheck = true
					break
				}
			}

			if skipMatchCheck {
				continue
			}

			pairs = append(pairs, struct {
				FirstPlayer  models.User
				SecondPlayer models.User
			}{FirstPlayer: player, SecondPlayer: opponent})

			usedPlayers[player.Username] = struct{}{}
			usedPlayers[opponent.Username] = struct{}{}
			break
		}
	}

	unusedList := make([]string, 0)
	for unusedPlayer := range allPlayersSet {
		if _, used := usedPlayers[unusedPlayer]; !used {
			unusedList = append(unusedList,
				fmt.Sprintf("Unused player: %s", unusedPlayer))
		}
	}

	response.Unused = unused

	for _, pair := range pairs {
		response.PairsNickname = append(response.PairsNickname,
			fmt.Sprintf("%s (%d) vs %s (%d)", pair.FirstPlayer.Username, pair.FirstPlayer.Rating, pair.SecondPlayer.Username, pair.SecondPlayer.Rating))

		response.PairsDiscord = append(response.PairsDiscord,
			fmt.Sprintf("<@%d> vs <@%d>", pair.FirstPlayer.DiscordId, pair.SecondPlayer.DiscordId))

		response.PairsRow = append(response.PairsRow,
			fmt.Sprintf("%s,%s", pair.FirstPlayer.Username, pair.SecondPlayer.Username))

		response.CreatedPairs = append(response.CreatedPairs, []string{
			pair.FirstPlayer.Username,
			pair.SecondPlayer.Username,
		})
	}

	return response, http.StatusOK, nil
}
