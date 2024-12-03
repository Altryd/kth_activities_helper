package models

import "time"

type Matches struct {
	Id             uint64           `gorm:"primaryKey;autoIncrement:true" json:"id"`
	MatchOsuID     uint64           `json:"match_osu_id"`
	MatchTypeId    uint64           `json:"match_type_id"`
	MatchType      MatchType        `gorm:"foreignKey:MatchTypeId" json:"match_type"`
	Date           time.Time        `gorm:"type:date" json:"date"`
	MatchUserScrim []MatchUserScrim `gorm:"foreignKey:MatchId;references:Id"`
	IsApproved     bool             `gorm:"default:false" json:"is_approved"`
}
