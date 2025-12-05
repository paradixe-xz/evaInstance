const SyncService = require('../services/syncService');
const Conversation = require('../models/Conversation');
const { Op } = require('sequelize');

class ConversationController {
  constructor() {
    this.syncService = new SyncService();
  }

  async syncConversations(req, res) {
    try {
      const results = await this.syncService.syncAllConversations();
      res.json({
        success: true,
        message: 'Sincronización completada',
        data: results
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        message: 'Error en la sincronización',
        error: error.message
      });
    }
  }

  async getConversations(req, res) {
    try {
      const { agent_name, agent_id } = req.query;
      let whereClause = {};
      
      // Filtrar por nombre de agente si se proporciona
      if (agent_name) {
        whereClause = {
          [Op.or]: [
            {
              'metadata.details.agent.name': {
                [Op.iLike]: `%${agent_name}%`
              }
            },
            {
              'metadata.original_data.agent_name': {
                [Op.iLike]: `%${agent_name}%`
              }
            }
          ]
        };
      }
      
      // Filtrar por ID de agente si se proporciona
      if (agent_id) {
        whereClause.agent_id = agent_id;
      }
      
      const conversations = await Conversation.findAll({
        where: whereClause,
        order: [['createdAt', 'DESC']]
      });
      
      res.json({
        success: true,
        data: conversations,
        count: conversations.length,
        filters: { agent_name, agent_id }
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        message: 'Error obteniendo conversaciones',
        error: error.message
      });
    }
  }

  async getConversationsByAgent(req, res) {
    try {
      const { agentName } = req.params;
      
      const conversations = await Conversation.findAll({
        where: {
          [Op.or]: [
            {
              'metadata.details.agent.name': {
                [Op.iLike]: `%${agentName}%`
              }
            },
            {
              'metadata.original_data.agent_name': {
                [Op.iLike]: `%${agentName}%`
              }
            }
          ]
        },
        order: [['createdAt', 'DESC']]
      });
      
      res.json({
        success: true,
        data: conversations,
        count: conversations.length,
        agent: agentName
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        message: 'Error obteniendo conversaciones por agente',
        error: error.message
      });
    }
  }

  async getAgents(req, res) {
    try {
      // Obtener todos los agentes únicos
      const conversations = await Conversation.findAll({
        attributes: ['agent_id', 'metadata'],
        group: ['agent_id', 'metadata']
      });
      
      const agents = conversations.map(conv => {
        const agentName = conv.metadata?.details?.agent?.name || 
                         conv.metadata?.original_data?.agent_name || 
                         'Sin nombre';
        return {
          agent_id: conv.agent_id,
          agent_name: agentName
        };
      }).filter((agent, index, self) => 
        index === self.findIndex(a => a.agent_id === agent.agent_id)
      );
      
      res.json({
        success: true,
        data: agents,
        count: agents.length
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        message: 'Error obteniendo agentes',
        error: error.message
      });
    }
  }

  async getConversationById(req, res) {
    try {
      const { id } = req.params;
      const conversation = await Conversation.findByPk(id);
      
      if (!conversation) {
        return res.status(404).json({
          success: false,
          message: 'Conversación no encontrada'
        });
      }

      res.json({
        success: true,
        data: conversation
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        message: 'Error obteniendo conversación',
        error: error.message
      });
    }
  }

  async getConversationAudio(req, res) {
    try {
      const { id } = req.params;
      const conversation = await Conversation.findByPk(id);
      
      if (!conversation || !conversation.audio_data) {
        return res.status(404).json({
          success: false,
          message: 'Audio no encontrado'
        });
      }

      res.set({
        'Content-Type': 'audio/mpeg',
        'Content-Disposition': `attachment; filename="conversation_${id}.mp3"`
      });
      
      res.send(conversation.audio_data);
    } catch (error) {
      res.status(500).json({
        success: false,
        message: 'Error obteniendo audio',
        error: error.message
      });
    }
  }
}

module.exports = ConversationController;