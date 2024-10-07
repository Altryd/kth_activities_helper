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

//TODO Все что ниже поместить в отдельный репозиторий

func (storage *Storage) CreateMatchType(matchTypeName string) (uint64, error) {
	matchTypeToCreate := models.MatchType{Name: matchTypeName}
	result := storage.db.Create(&matchTypeToCreate)
	if result.Error != nil {
		return 0, result.Error
	}

	return matchTypeToCreate.ID, nil
}

//func (storage *Storage) GetMatchTypes(matchTypeId uint64) (string, error) {
//	result := storage.db.Get()
//	if result.Error != nil {
//		return "", result.Error
//	}
//
//	return result., nil
//}

func (storage *Storage) CreateMatch(matchId uint64, matchTypeId uint64, matchDate time.Time) (uint64, error) {
	matchToCreate := models.Matches{Id: matchId, MatchTypeId: matchTypeId, Date: matchDate}
	result := storage.db.Create(&matchToCreate)
	if result.Error != nil {
		return 0, result.Error
	}
	return matchToCreate.Id, nil
}
