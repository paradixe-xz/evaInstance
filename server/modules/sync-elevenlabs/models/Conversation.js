const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');

const Conversation = sequelize.define('Conversation', {
  id: {
    type: DataTypes.STRING,
    primaryKey: true,
    allowNull: false
  },
  lead_number: {
    type: DataTypes.STRING,
    allowNull: true
  },
  agent_id: {
    type: DataTypes.STRING,
    allowNull: true
  },
  conversation_id: {
    type: DataTypes.STRING,
    allowNull: false
  },
  status: {
    type: DataTypes.STRING,
    allowNull: true
  },
  evaluation_criteria_result: {
    type: DataTypes.STRING,
    allowNull: true
  },
  evaluation_criteria_rationale: {
    type: DataTypes.STRING,
    allowNull: true
  },
  data_collection_client_type: {
    type: DataTypes.STRING,
    allowNull: true
  },
  data_collection_meta: {
    type: DataTypes.STRING,
    allowNull: true
  },
  data_collection_emb: {
    type: DataTypes.STRING,
    allowNull: true
  },
  data_collection_result_call: {
    type: DataTypes.STRING,
    allowNull: true
  },
  data_collection_cuota: {
    type: DataTypes.STRING,
    allowNull: true
  },
  data_collection_edad: {
    type: DataTypes.STRING,
    allowNull: true
  },
  data_collection_ok: {
    type: DataTypes.STRING,
    allowNull: true
  },
  data_collection_number: {
    type: DataTypes.STRING,
    allowNull: true
  },
  data_collection_neto: {
    type: DataTypes.STRING,
    allowNull: true
  },
  data_collection_canal: {
    type: DataTypes.STRING,
    allowNull: true
  },
  data_collection_mot: {
    type: DataTypes.STRING,
    allowNull: true
  },
  transcript: {
    type: DataTypes.JSON, // Cambiar a TEXT para permitir transcripts largos
    allowNull: true
  }
}, {
  tableName: 'conversations',
  timestamps: false
});

module.exports = Conversation;