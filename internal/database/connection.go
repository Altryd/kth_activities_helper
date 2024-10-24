package database

import (
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"kth_activities_helper/internal/config"
	"kth_activities_helper/internal/models"
	"log/slog"
	"strconv"
	"time"
)

type Storage struct {
	db *gorm.DB
}

func createConnectionString(cfg *config.Config) string {
	return "host=" + cfg.DatabaseConfig.Address +
		" user=" + cfg.DatabaseConfig.User +
		" password=" + cfg.DatabaseConfig.Pass +
		" dbname=" + cfg.DatabaseConfig.Database +
		" port=" + strconv.Itoa(cfg.DatabaseConfig.Port) +
		" sslmode=" + cfg.DatabaseConfig.SSLmode
}

func New(cfg *config.Config, log *slog.Logger) (*Storage, error) {
	dsn := createConnectionString(cfg)
	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})
	if err != nil {
		log.Error("Failed to connect to database", err.Error())
		return nil, err
	}
	err = db.AutoMigrate(&models.MatchType{}, &models.Matches{}, &models.User{}, &models.MatchUserScrim{})
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
	result := storage.db.Find(&matches)
	if result.Error != nil {
		return nil, result.Error
	}
	return matches, nil
}

func (storage *Storage) SelectOneMatch(id uint64) (models.Matches, error) {
	match := models.Matches{}
	result := storage.db.First(&match, id)
	if result.Error != nil {
		return models.Matches{}, result.Error
	}
	return match, nil
}

func (storage *Storage) CreateMatch(matchId uint64, matchTypeId uint64, matchDate time.Time) (uint64, error) {
	matchToCreate := models.Matches{Id: matchId, MatchTypeId: matchTypeId, Date: matchDate}
	result := storage.db.Create(&matchToCreate)
	if result.Error != nil {
		return 0, result.Error
	}
	return matchToCreate.Id, nil
}

func (storage *Storage) EditMatch(matchId uint64, matchTypeId uint64, matchDate time.Time, isApproved bool) (models.Matches, error) {
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
	result := storage.db.First(&user, osuId)
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
func (storage *Storage) CreateMatchUserScrim(playerId uint64, matchId uint64, score uint64, isBlue bool) (uint64, uint64, error) {
	matchUserScrimToCreate := models.MatchUserScrim{PlayerId: playerId, MatchId: matchId, Score: score, IsBlue: isBlue}
	result := storage.db.Create(&matchUserScrimToCreate)
	if result.Error != nil {
		return 0, 0, result.Error
	}
	return matchUserScrimToCreate.PlayerId, matchUserScrimToCreate.MatchId, nil
}
